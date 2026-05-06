import traceback
from fastapi import HTTPException
from models.insights_model import Insights
from models.documentation_model import Documentation
from utils.logger import log_event
from utils.helper import clean_ai_response
from graph.builder import build_documentation_graph

SERVICE_NAME = "documentation_service"


async def generate_documentation_service(payload):
    try:
        insights_id = payload.insights_id

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate_documentation_service",
            message="Documentation generation started",
            metadata={"insights_id": insights_id}
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

        result = await graph.ainvoke({
            "user_input": {
                "requirements": requirements_input,
                "code": code_for_prompt,
                "tests": tests_content
            }
        })

        raw_ai = result.get("ai_response")

        if not raw_ai:
            raise HTTPException(status_code=500, detail="Invalid AI response")

        if isinstance(raw_ai, dict):
            doc_data = raw_ai
        else:
            doc_data = clean_ai_response(str(raw_ai))

        if not doc_data:
            log_event(
                level="ERROR",
                service=SERVICE_NAME,
                function="generate_documentation_service",
                message="Invalid documentation format from AI",
                metadata={"raw_response": raw_ai}
            )
            raise HTTPException(status_code=500, detail="Invalid documentation format")

        doc_obj = await Documentation.create(
            insights_id=insights_id,
            is_completed=True,
            **doc_data
        )

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate_documentation_service",
            message="Documentation stored successfully",
            metadata={"doc_id": doc_obj.id}
        )

        return {
            "doc_id": doc_obj.id,
            "overview": doc_obj.overview,
            "architecture": doc_obj.architecture,
            "file_responsibilities": doc_obj.file_responsibilities,
            "functional_requirements": doc_obj.functional_requirements,
            "non_functional_requirements": doc_obj.non_functional_requirements,
            "tech_stack_used": doc_obj.tech_stack_used,
            "assumptions": doc_obj.assumptions,
            "test_summary": doc_obj.test_summary,
            "next_steps": doc_obj.next_steps,
        }

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="generate_documentation_service",
            message="Documentation generation failed",
            metadata={"trace": traceback.format_exc()}
        )
        raise HTTPException(status_code=500, detail="Internal server error")

async def get_documentation_service(documentation_id: int):
    try:
        log_event(
            level="INFO", 
            service=SERVICE_NAME, 
            function="get_documentation_service",
            message="Fetching documentation", 
            metadata={"documentation_id": documentation_id})

        doc = await Documentation.get_or_none(id=documentation_id)

        if not doc:
            raise HTTPException(status_code=404, detail="Documentation not found")

        return {
            "doc_id": doc.id,
            "overview": doc.overview,
            "architecture": doc.architecture,
            "file_responsibilities": doc.file_responsibilities,
            "functional_requirements": doc.functional_requirements,
            "non_functional_requirements": doc.non_functional_requirements,
            "tech_stack_used": doc.tech_stack_used,
            "assumptions": doc.assumptions,
            "test_summary": doc.test_summary,
            "next_steps": doc.next_steps,
        }

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR", 
            service=SERVICE_NAME, 
            function="get_documentation_service",
            message="Failed to fetch documentation", 
            metadata={"trace": traceback.format_exc()}
            )
        raise HTTPException(status_code=500, detail="Internal server error")