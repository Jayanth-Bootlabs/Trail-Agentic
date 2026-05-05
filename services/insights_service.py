import traceback
import json
import inspect
from fastapi import HTTPException
from schemas.insights_schema import GenerateInsightsRequest
from models.validation_model import ValidationSession
from models.code_model import GeneratedCode
from models.unit_tests_model import UnitTests
from models.insights_model import Insights
from prompts.insights_prompt import get_insights_prompt
from utils.gemini_llm import GeminiLLM
from utils.logger import log_event

SERVICE_NAME = "insights_service"


async def generate_insights_service(payload: GenerateInsightsRequest):
    try:
        user_id = payload.user_id
        session_id = payload.session_id

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate_insights_service",
            message="Insights generation started",
            metadata={"user_id": user_id, "session_id": session_id}
        )

        session = await ValidationSession.get_or_none(id=session_id, user_id=user_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        code_record = await GeneratedCode.filter(session_id=session_id).first()

        if not code_record:
            raise HTTPException(status_code=404, detail="Generated code not found")

        tests_record = await UnitTests.filter(session_id=session_id).first()

        
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

        tests_content = getattr(tests_record, "test_code", "") if tests_record else ""

        prompt = get_insights_prompt(
            requirements_json=session.user_input,
            code_content=code_content,
            test_content=tests_content
        )

        llm = GeminiLLM()
        response = llm.invoke(prompt)

        if inspect.isawaitable(response):
            response = await response

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
            user_id=user_id,
            session_id=session_id,
            code_id=code_record.id,
            tests_id=tests_record.id if tests_record else None,
            **insights_data
        )

        return insight_obj

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
    


async def get_insights_service(user_id: int, session_id: int):
    try:
        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="get_insights_service",
            message="Fetching insights",
            metadata={"user_id": user_id, "session_id": session_id},
        )

        insights = await Insights.filter(user_id=user_id,session_id=session_id).first()

        if not insights:
            raise HTTPException(status_code=404, detail="Insights not found")

        return insights

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="get_insights_service",
            message="Failed to fetch insights",
            metadata={"trace": traceback.format_exc()},
        )
        raise HTTPException(status_code=500, detail="Internal server error")