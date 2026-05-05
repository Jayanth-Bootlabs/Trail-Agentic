import traceback
import json
from fastapi import HTTPException
from models.validation_model import ValidationSession
from models.code_model import GeneratedCode
from prompts.code_prompt import get_code_prompt
from utils.gemini_llm import llm
from utils.logger import log_event

SERVICE_NAME = "code_generation_service"


async def generate_code_service(user_id: int, session_id: int):
    try:
        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate_code_service",
            message="Code generation started",
            metadata={"user_id": user_id, "session_id": session_id},
        )

        session = await ValidationSession.get_or_none(
            id=session_id,
            user_id=user_id,
            is_completed=True
        )

        if not session:
            raise HTTPException(status_code=404, detail="Valid session not found")

        prompt = get_code_prompt(session.combined_input)
        response = await llm.generate(prompt)

        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.endswith("```"):
            response = response[:-3]

        code_data = json.loads(response)

        code_obj = await GeneratedCode.create(
            user_id=user_id,
            session_id=session_id,
            code_json=code_data
        )

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate_code_service",
            message="Code stored successfully",
            metadata={"code_id": code_obj.id},
        )

        return {
            "code_id": code_obj.id,
            "session_id": session_id,
            "source_code": code_data.get("source_code", {}),
        }

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="generate_code_service",
            message="Code generation failed",
            stack_trace=traceback.format_exc(),
        )
        raise

async def get_generated_code_service(user_id: int, session_id: int):
    try:
        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="get_generated_code_service",
            message="Fetching generated code",
            metadata={"user_id": user_id, "session_id": session_id},
        )

        code_record = await GeneratedCode.filter(user_id=user_id,session_id=session_id).first()

        if not code_record:
            raise HTTPException(status_code=404, detail="Generated code not found")

        code_data = code_record.code_json or {}

        return {
            "code_id": code_record.id,
            "user_id": code_record.user_id,
            "session_id": code_record.session_id,
            "project_title": code_data.get("project_title", ""),
            "tech_stack": code_data.get("tech_stack", []),
            "file_structure": code_data.get("file_structure", []),
            "source_code": code_data.get("source_code", {}),
            "created_at": str(code_record.created_at) if hasattr(code_record, "created_at") else None,
        }

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="get_generated_code_service",
            message="Fetching code failed",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")