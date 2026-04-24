import traceback
from fastapi import Request, HTTPException
from models.prompt_validator_model import PromptSession
from utils.logger import log_event
from utils.helper import clean_ai_response
from graph.graph_builder import build_validation_graph

SERVICE_NAME = "validation_service"

async def run_prompt_service(payload, request: Request):
    try:
        user_input = payload.user_input

        user = request.state.user
        if not user:
            raise HTTPException(status_code=400, detail="User not found")

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="run_prompt_service",
            message="Validation started",
            metadata={"user_id": user.id},
        )

        # 1. Build graph
        graph = build_validation_graph()

        # 2. Initial state
        state = {
            "user_input": user_input,
            "status": "start",
        }

        # 3. Execute graph
        result = await graph.ainvoke(state)

        raw_output = result.get("ai_response")

        if not raw_output:
            raise ValueError("Empty response from LLM")

        cleaned_output = clean_ai_response(raw_output)

        if not isinstance(cleaned_output, dict):
            cleaned_output = {
                "status": "error",
                "message": "Invalid AI response format"
            }

        status = cleaned_output.get("status")
        message = cleaned_output.get("message", "")

        is_completed = status == "valid"

        session = await PromptSession.create(
            user=user,
            user_input=user_input,
            ai_response=str(cleaned_output),
            is_completed=is_completed
        )

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="run_prompt_service",
            message="Validation completed",
            metadata={
                "session_id": session.id,
                "status": status,
            },
        )

        if status == "question":
            return {
                "session_id": session.id,
                "message": message,
                "is_completed": False
            }

        if status == "valid":
            return {
                "session_id": session.id,
                "message": "Input is valid. Proceeding to next step.",
                "is_completed": True,
                "user_input": user_input
            }

        return {
            "session_id": session.id,
            "message": "Something went wrong",
            "is_completed": False
        }

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="run_prompt_service",
            message="Validation failed",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")