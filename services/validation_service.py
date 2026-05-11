import traceback
from fastapi import HTTPException
from builder.validation_builder import build_validation_graph
from models.validation_model import ValidationSession
from utils.logger import log_event

SERVICE_NAME = "validation_service"

async def validate_prompt_request(payload, user):
    try:
        user_input = payload.user_input

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="validate_prompt_request",
            message="Starting prompt validation",
            metadata={
                "user_id": user.id,
                "email": user.email,
                "user_input": user_input
            },
        )

        graph = build_validation_graph()

        config = {
            "configurable": {
                "thread_id": f"user-{user.id}"
            }
        }

        result = await graph.ainvoke(
            {
                "user_input": user_input,
                "history": [],
                "attempts": 0,
                "messages": [],
                "reasoning": [],
                "retry_count": 0
            },
            config=config
        )

        ai = result.get("ai_response", {})

        session = await ValidationSession.create(
            user=user,
            user_input=user_input,
            status=result.get("status"),
            ai_response=ai,
            is_completed=(result.get("status") == "valid"),
        )

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="validate_prompt_request",
            message="Validation session created",
            metadata={
                "session_id": session.id,
                "user_id": user.id,
                "status": result.get("status")
            },
        )

        return {
            "session_id": session.id,
            "status": result.get("status"),
            "message": ai.get("message"),
            "user_input": user_input,
        }

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="validate_prompt_request",
            message="Validation crashed",
            metadata={
                "user_id": user.id if user else None
            },
            stack_trace=traceback.format_exc(),
        )

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )