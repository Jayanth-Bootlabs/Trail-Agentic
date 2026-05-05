import traceback
import json
import inspect
from fastapi import HTTPException
from schemas.documentation_schema import GenerateDocumentationRequest
from models.validation_model import ValidationSession
from models.code_model import GeneratedCode
from models.unit_tests_model import UnitTests
from models.documentation_model import Documentation
from prompts.documentation_prompt import get_documentation_prompt
from utils.gemini_llm import GeminiLLM
from utils.logger import log_event

SERVICE_NAME = "documentation_service"


async def generate_documentation_service(payload: GenerateDocumentationRequest):
    try:
        user_id = payload.user_id
        session_id = payload.session_id

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate_documentation_service",
            message="Documentation generation started",
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

        code_for_prompt = code_payload if isinstance(code_payload, dict) else str(code_payload)
        tests_content = getattr(tests_record, "test_code", "") if tests_record else ""

       
        prompt = get_documentation_prompt(session.user_input, code_for_prompt, tests_content)

        llm = GeminiLLM()
        response = llm.invoke(prompt)

        if inspect.isawaitable(response):
            response = await response

        if not response:
            raise HTTPException(status_code=500, detail="Empty response from LLM")

        cleaned = response.strip().replace("```json", "").replace("```", "")

        try:
            doc_data = json.loads(cleaned)

        except Exception:
            log_event(
                level="ERROR",
                service=SERVICE_NAME,
                function="generate_documentation_service",
                message="Failed to parse AI response for documentation",
                metadata={"raw_response": cleaned}
            )
            raise HTTPException(status_code=500, detail="Invalid documentation format from AI")

        doc_obj = await Documentation.create(
            user_id=user_id,
            session_id=session_id,
            code_id=code_record.id,
            tests_id=tests_record.id if tests_record else None,
            **doc_data
        )

        return doc_obj

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
    

async def get_documentation_service(user_id: int, session_id: int):
    try:
        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="get_documentation_service",
            message="Fetching documentation",
            metadata={"user_id": user_id, "session_id": session_id},
        )

        doc = await Documentation.filter(user_id=user_id,session_id=session_id).first()

        if not doc:
            raise HTTPException(status_code=404, detail="Documentation not found")

        return doc

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