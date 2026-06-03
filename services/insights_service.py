import traceback
import json
from fastapi import HTTPException
from builder.insights_builder import build_insights_graph
from schemas.insights_schema import GenerateInsightsRequest
from models.unit_tests_model import UnitTests
from models.insights_model import Insights
from utils.logger import log_event
from utils.cache import get_redis

SERVICE_NAME = "insights_service"


async def generate_insights_service(payload: GenerateInsightsRequest):
    try:
        unit_test_id = payload.unit_test_id

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate_insights_service",
            message="Starting insights generation",
            metadata={"unit_test_id": unit_test_id},
        )

        existing_insight = await Insights.get_or_none(
            tests_id=unit_test_id,
            is_completed=True
        )

        if existing_insight:
            raise HTTPException(
                status_code=409,
                detail="Insights already generated for this unit test id"
            )

        tests_record = await UnitTests.filter(
            id=unit_test_id,
            is_completed=True
        ).prefetch_related("code__requirement").first()

        if not tests_record:
            raise HTTPException(
                status_code=404,
                detail="Unit test not found or not completed"
            )

        code_record = tests_record.code
        requirement_record = code_record.requirement

        graph = build_insights_graph()

        config = {
            "configurable": {
                "thread_id": f"insights-{unit_test_id}"
            }
        }

        result = await graph.ainvoke(
            {
                "requirements": requirement_record.user_input,
                "code": code_record.code_json,
                "test_code": tests_record.test_code,
                "retry_count": 0
            },
            config=config
        )

        ai = result.get("insights", {})

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate_insights_service",
            message="Insights data from state",
            metadata={"ai_keys": list(ai.keys()) if ai else []},
        )

        insight_obj = await Insights.create(
            tests=tests_record,
            insights_summary=ai.get("insights_summary", ""),
            key_insights=ai.get("key_insights", []),
            missing_implementations=ai.get("missing_implementations", []),
            code_quality_issues=ai.get("code_quality_issues", []),
            security_issues=ai.get("security_issues", []),
            scalability_problems=ai.get("scalability_problems", []),
            refactoring_suggestions=ai.get("refactoring_suggestions", []),
            dependencies=ai.get("dependencies", []),
            recommendations=ai.get("recommendations", []),
            is_completed=(result.get("status") == "valid"),
        )

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate_insights_service",
            message="Insights record created",
            metadata={
                "insight_id": insight_obj.id,
                "unit_test_id": unit_test_id,
                "status": result.get("status"),
            },
        )

        return {
            "insight_id": insight_obj.id,
            "unit_test_id": unit_test_id,
            "insights_summary": insight_obj.insights_summary,
            "key_insights": insight_obj.key_insights,
            "missing_implementations": insight_obj.missing_implementations,
            "code_quality_issues": insight_obj.code_quality_issues,
            "security_issues": insight_obj.security_issues,
            "scalability_problems": insight_obj.scalability_problems,
            "refactoring_suggestions": insight_obj.refactoring_suggestions,
            "dependencies": insight_obj.dependencies,
            "recommendations": insight_obj.recommendations,
            "is_completed": insight_obj.is_completed,
            "created_at": str(insight_obj.created_at) if insight_obj.created_at else None,
            "status": result.get("status"),
        }

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="generate_insights_service",
            message="Insights generation crashed",
            metadata={"trace": traceback.format_exc()},
        )

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
    

async def get_insights_service(insights_id: int):
    try:
        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="get_insights_service",
            message="Fetching insights",
            metadata={"insights_id": insights_id},
        )

        # check cache first
        redis = await get_redis()

        if redis:
            cache_key = f"insights:{insights_id}"
            cached = await redis.get(cache_key)
            
        cache_key = f"insights:{insights_id}"
        cached = await redis.get(cache_key)

        if cached:
            log_event(
                level="INFO",
                service=SERVICE_NAME,
                function="get_insights_service",
                message="Cache hit",
                metadata={"insights_id": insights_id},
            )
            return json.loads(cached)

        # cache miss — fetch from DB
        insight = await Insights.get_or_none(id=insights_id)

        if not insight:
            raise HTTPException(status_code=404, detail="Insights not found")

        result = {
            "insight_id": insight.id,
            "unit_test_id": insight.tests_id,
            "insights_summary": insight.insights_summary,
            "key_insights": insight.key_insights,
            "missing_implementations": insight.missing_implementations,
            "code_quality_issues": insight.code_quality_issues,
            "security_issues": insight.security_issues,
            "scalability_problems": insight.scalability_problems,
            "refactoring_suggestions": insight.refactoring_suggestions,
            "dependencies": insight.dependencies,
            "recommendations": insight.recommendations,
            "is_completed": insight.is_completed,
            "created_at": str(insight.created_at) if insight.created_at else None,
        }

        # store in cache for 1 hour
        await redis.set(cache_key, json.dumps(result), ex=3600)

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="get_insights_service",
            message="Cache miss — stored in cache",
            metadata={"insights_id": insights_id},
        )

        return result

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="get_insights_service",
            message="Fetching insights failed",
            metadata={"trace": traceback.format_exc()},
        )
        raise HTTPException(status_code=500, detail="Internal server error")