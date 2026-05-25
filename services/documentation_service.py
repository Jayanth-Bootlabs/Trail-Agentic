import traceback
import json
from fastapi import HTTPException
from builder.documentation_builder import build_documentation_graph
from schemas.documentation_schema import GenerateDocumentationRequest
from models.insights_model import Insights
from models.documentation_model import Documentation
from utils.logger import log_event
from utils.cache import get_redis

SERVICE_NAME = "documentation_service"


async def generate_documentation_service(payload: GenerateDocumentationRequest):
    try:
        insights_id = payload.insights_id

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate_documentation_service",
            message="Documentation generation started",
            metadata={"insights_id": insights_id},
        )

        insights_record = await Insights.filter(
            id=insights_id,
            is_completed=True
        ).prefetch_related("tests__code__requirement").first()

        if not insights_record:
            raise HTTPException(
                status_code=404,
                detail="Insights not found or insights generation is not completed yet"
            )

        tests_record = insights_record.tests
        if not tests_record:
            raise HTTPException(status_code=404, detail="Unit tests not found")

        code_record = tests_record.code
        if not code_record:
            raise HTTPException(status_code=404, detail="Generated code not found")

        requirement_record = code_record.requirement
        if not requirement_record:
            raise HTTPException(status_code=404, detail="Requirement session not found")

        code_payload = getattr(code_record, "code_json", None)
        if code_payload is None:
            raise HTTPException(status_code=500, detail="Generated code payload is empty")

        code_for_prompt = code_payload if isinstance(code_payload, dict) else str(code_payload)
        tests_content = getattr(tests_record, "test_code", "") or ""
        requirements_input = requirement_record.user_input

        graph = build_documentation_graph()

        config = {
            "configurable": {
                "thread_id": f"documentation-{insights_id}"
            }
        }

        result = await graph.ainvoke(
            {
                "requirements": requirements_input,
                "code": code_for_prompt,
                "test_code": tests_content,
                "history": [],
                "attempts": 0,
                "messages": [],
                "reasoning": [],
                "retry_count": 0
            },
            config=config
        )

        ai = result.get("documentation", {})

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate_documentation_service",
            message="Documentation data from state",
            metadata={"ai_keys": list(ai.keys()) if ai else []},
        )

        doc_obj = await Documentation.create(
            insights=insights_record,
            overview=ai.get("overview", ""),
            architecture=ai.get("architecture", ""),
            file_responsibilities=ai.get("file_responsibilities", []),
            functional_requirements=ai.get("functional_requirements", []),
            non_functional_requirements=ai.get("non_functional_requirements", []),
            tech_stack_used=ai.get("tech_stack_used", []),
            assumptions=ai.get("assumptions", []),
            test_summary=ai.get("test_summary", ""),
            next_steps=ai.get("next_steps", []),
            is_completed=(result.get("status") == "valid"),
        )

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate_documentation_service",
            message="Documentation stored successfully",
            metadata={
                "doc_id": doc_obj.id,
                "insights_id": insights_id,
                "status": result.get("status"),
            },
        )

        return {
            "doc_id": doc_obj.id,
            "insights_id": insights_id,
            "overview": doc_obj.overview,
            "architecture": doc_obj.architecture,
            "file_responsibilities": doc_obj.file_responsibilities,
            "functional_requirements": doc_obj.functional_requirements,
            "non_functional_requirements": doc_obj.non_functional_requirements,
            "tech_stack_used": doc_obj.tech_stack_used,
            "assumptions": doc_obj.assumptions,
            "test_summary": doc_obj.test_summary,
            "next_steps": doc_obj.next_steps,
            "is_completed": doc_obj.is_completed,
            "created_at": str(doc_obj.created_at) if doc_obj.created_at else None,
            "status": result.get("status"),
        }

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="generate_documentation_service",
            message="Documentation generation failed",
            metadata={"trace": traceback.format_exc()},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


async def get_documentation_service(documentation_id: int):
    try:
        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="get_documentation_service",
            message="Fetching documentation",
            metadata={"documentation_id": documentation_id},
        )

        # check cache first
        redis = await get_redis()

        if redis:
            cache_key = f"documentation:{documentation_id}"
            cached = await redis.get(cache_key)

        cache_key = f"documentation:{documentation_id}"
        cached = await redis.get(cache_key)

        if cached:
            log_event(
                level="INFO",
                service=SERVICE_NAME,
                function="get_documentation_service",
                message="Cache hit",
                metadata={"documentation_id": documentation_id},
            )
            return json.loads(cached)

        # cache miss — fetch from DB
        doc = await Documentation.get_or_none(id=documentation_id)

        if not doc:
            raise HTTPException(status_code=404, detail="Documentation not found")

        result = {
            "doc_id": doc.id,
            "insights_id": doc.insights_id,
            "overview": doc.overview,
            "architecture": doc.architecture,
            "file_responsibilities": doc.file_responsibilities,
            "functional_requirements": doc.functional_requirements,
            "non_functional_requirements": doc.non_functional_requirements,
            "tech_stack_used": doc.tech_stack_used,
            "assumptions": doc.assumptions,
            "test_summary": doc.test_summary,
            "next_steps": doc.next_steps,
            "is_completed": doc.is_completed,
            "created_at": str(doc.created_at) if doc.created_at else None,
        }

        # store in cache for 1 hour
        await redis.set(cache_key, json.dumps(result), ex=3600)

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="get_documentation_service",
            message="Cache miss — stored in cache",
            metadata={"documentation_id": documentation_id},
        )

        return result

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="get_documentation_service",
            message="Failed to fetch documentation",
            metadata={"trace": traceback.format_exc()},
        )
        raise HTTPException(status_code=500, detail="Internal server error")