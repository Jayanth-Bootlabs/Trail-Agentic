import json
import traceback
from fastapi import HTTPException
from models.unit_tests_model import UnitTests
from schemas.insights_schema import GenerateInsightsRequest
from models.insights_model import Insights
from utils.logger import log_event
from graph.builder import build_insights_graph

SERVICE_NAME = "insights_service"

async def generate_insights_service(payload: GenerateInsightsRequest):
    try:
        unit_test_id = payload.unit_test_id

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate_insights_service",
            message="Insights generation started",
            metadata={"unit_test_id": unit_test_id}
        )

        tests_record = await UnitTests.filter(
            id=unit_test_id,
            is_completed=True
        ).prefetch_related("code__requirement").first()

        if not tests_record:
            raise HTTPException(
                status_code=404,
                detail="Unit test not found or unit test generation is not completed yet"
            )

        code_record = tests_record.code
        if not code_record:
            raise HTTPException(status_code=404, detail="Generated code not found")

        requirement_record = code_record.requirement
        if not requirement_record:
            raise HTTPException(status_code=404, detail="Requirement session not found")

        code_payload = getattr(code_record, "code_json", None)

        if code_payload is None:
            raise HTTPException(status_code=500, detail="Generated code payload is empty")

        if isinstance(code_payload, dict):
            code_content = (
                code_payload.get("code")
                or code_payload.get("source_code")
                or code_payload.get("content")
                or json.dumps(code_payload)
            )
        else:
            code_content = str(code_payload)

        tests_content = getattr(tests_record, "test_code", "") or ""

        graph = build_insights_graph()

        result = await graph.ainvoke({
            "user_input": {
                "requirements": requirement_record.user_input,
                "code": code_content,
                "tests": tests_content
            }
        })

        response = result.get("ai_response")

        insights_data = None

        if isinstance(response, dict):
            insights_data = response

        elif isinstance(response, str):
            cleaned = response.strip().replace("```json", "").replace("```", "")

            try:
                insights_data = json.loads(cleaned)

            except Exception:
                log_event(
                    level="ERROR",
                    service=SERVICE_NAME,
                    function="generate_insights_service",
                    message="Failed to parse AI response for insights",
                    metadata={"raw_response": cleaned}
                )
                raise HTTPException(status_code=500, detail="Invalid AI response format")

        else:
            raise HTTPException(status_code=500, detail="Invalid AI response type")

        insight_obj = await Insights.create(
            tests_id=unit_test_id,
            is_completed=True,
            **insights_data
        )

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate_insights_service",
            message="Insights stored successfully",
            metadata={"insight_id": insight_obj.id}
        )

        return {
            "insight_id": insight_obj.id,
            "insights_summary": insight_obj.insights_summary,
            "key_insights": insight_obj.key_insights,
            "missing_implementations": insight_obj.missing_implementations,
            "code_quality_issues": insight_obj.code_quality_issues,
            "security_issues": insight_obj.security_issues,
            "scalability_problems": insight_obj.scalability_problems,
            "refactoring_suggestions": insight_obj.refactoring_suggestions,
            "dependencies": insight_obj.dependencies,
            "recommendations": insight_obj.recommendations,
        }

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="generate_insights_service",
            message="Insights generation failed",
            metadata={"trace": traceback.format_exc()}
        )
        raise HTTPException(status_code=500, detail="Internal server error")

async def get_insights_service(insights_id: int):
    try:
        log_event(
            level="INFO", 
            service=SERVICE_NAME, 
            function="get_insights_service",
            message="Fetching insights", 
            metadata={"insights_id": insights_id}
            )

        insights = await Insights.get_or_none(id=insights_id)

        if not insights:
            raise HTTPException(status_code=404, detail="Insights not found")

        return {
            "insight_id": insights.id,
            "insights_summary": insights.insights_summary,
            "key_insights": insights.key_insights,
            "missing_implementations": insights.missing_implementations,
            "code_quality_issues": insights.code_quality_issues,
            "security_issues": insights.security_issues,
            "scalability_problems": insights.scalability_problems,
            "refactoring_suggestions": insights.refactoring_suggestions,
            "dependencies": insights.dependencies,
            "recommendations": insights.recommendations,
        }

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR", 
            service=SERVICE_NAME, 
            function="get_insights_service",
            message="Failed to fetch insights", 
            metadata={"trace": traceback.format_exc()}
            )
        raise HTTPException(status_code=500, detail="Internal server error")