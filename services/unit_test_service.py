import traceback
import json
from fastapi import HTTPException
from schemas.unit_test_schema import UnitTestRequest
from models.validation_model import ValidationSession
from models.code_model import GeneratedCode
from models.unit_tests_model import UnitTests
from graph.builder import build_unit_tests_graph
from utils.logger import log_event
from utils.helper import clean_ai_response

SERVICE_NAME = "unit_tests_service"


async def generate_unit_tests_service(payload: UnitTestRequest):
    try:
        user_id = payload.user_id
        session_id = payload.session_id

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate_unit_tests_service",
            message="Unit test generation started",
            metadata={"user_id": user_id, "session_id": session_id}
        )

        
        session = await ValidationSession.get_or_none(id=session_id, user_id=user_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        
        code_record = await GeneratedCode.filter(session_id=session_id).first()

        if not code_record:
            raise HTTPException(status_code=404, detail="Generated code not found")

        
        code_payload = getattr(code_record, "code_json", None)

        if code_payload is None:
            raise HTTPException(status_code=500, detail="Generated code payload is empty")

        if isinstance(code_payload, dict):
            user_input = (
                code_payload.get("code")
                or code_payload.get("source_code")
                or code_payload.get("generated_code")
                or code_payload.get("content")
                or code_payload
            )
        else:
            user_input = code_payload

        if not user_input:
            raise HTTPException(status_code=500, detail="Generated code is empty")

     
        graph = build_unit_tests_graph()
        result = await graph.ainvoke({"session_id": session_id, "user_input": user_input})

        raw_ai = result.get("ai_response")

        if not raw_ai:
            raise HTTPException(status_code=500, detail="Invalid AI response")

        
        parsed_ai = None

        if isinstance(raw_ai, dict):
            parsed_ai = raw_ai

        elif isinstance(raw_ai, str):
            parsed_ai = clean_ai_response(raw_ai) or None

            if parsed_ai is None:
                try:
                    parsed_ai = json.loads(raw_ai)
                except Exception:
                    parsed_ai = {"test_code": raw_ai}
        else:
            parsed_ai = {"test_code": str(raw_ai)}

       
        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate_unit_tests_service",
            message="AI response parsed for unit tests",
            metadata={"parsed_keys": list(parsed_ai.keys()) if isinstance(parsed_ai, dict) else None}
        )

        
        if isinstance(parsed_ai, dict):
            test_code = parsed_ai.get("test_code") or ""

            test_summary = parsed_ai.get("test_summary") or ""

            frameworks_used = parsed_ai.get("frameworks_used") or []

        else:
            test_code = str(parsed_ai)
            test_summary = ""
            frameworks_used = []

        
        test_obj = await UnitTests.create(
            user_id=user_id,
            session_id=session_id,
            code_id=code_record.id,
            test_code=test_code,
            test_summary=test_summary,
            frameworks_used=frameworks_used
        )

        return test_obj

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="generate_unit_tests_service",
            message="Unit test generation failed",
            metadata={"trace": traceback.format_exc()}
        )
        raise HTTPException(status_code=500, detail="Internal server error")
    

async def get_unit_tests_service(user_id: int, session_id: int):
    try:
        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="get_unit_tests_service",
            message="Fetching unit tests",
            metadata={"user_id": user_id, "session_id": session_id},
        )

        test_record = await UnitTests.filter(user_id=user_id,session_id=session_id).first()

        if not test_record:
            raise HTTPException(status_code=404, detail="Unit tests not found")

        return {
            "test_id": test_record.id,
            "user_id": test_record.user_id,
            "session_id": test_record.session_id,
            "code_id": test_record.code_id,
            "test_code": test_record.test_code or "",
            "test_summary": test_record.test_summary or "",
            "frameworks_used": test_record.frameworks_used or [],
            "created_at": str(test_record.created_at) if hasattr(test_record, "created_at") else None,
        }

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="get_unit_tests_service",
            message="Fetching unit tests failed",
            metadata={"trace": traceback.format_exc()},
        )
        raise HTTPException(status_code=500, detail="Internal server error")