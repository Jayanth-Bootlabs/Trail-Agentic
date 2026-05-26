import traceback
import uuid

from fastapi import HTTPException
from tortoise import connections

from builder.validation_builder import build_validation_graph
from models.validation_model import ValidationSession
from utils.logger import log_event


SERVICE_NAME = "validation_service"


async def validate_prompt_request(payload, user):

    try:

        user_input = payload.user_input.strip()

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
                "thread_id": f"validation-{user.id}-{uuid.uuid4().hex}"
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

        ai = result.get("ai_response") or {}

        session = await ValidationSession.create(
            user=user,
            user_input=user_input,
            combined_input=user_input,
            status=result.get("status"),
            ai_response=ai,
            is_completed=(
                result.get("status") == "valid"
            ),
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


async def continue_prompt_request(payload, user):

    try:

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="continue_prompt_request",
            message="Continuing validation",
            metadata={
                "user_id": user.id,
                "session_id": payload.session_id
            },
        )

        session = await ValidationSession.get_or_none(
            id=payload.session_id,
            user=user
        )

        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )

        if session.status != "clarify":
            raise HTTPException(
                status_code=400,
                detail="This session does not require clarification"
            )

        previous_input = (
            session.combined_input
            if session.combined_input
            else session.user_input
        )

        user_reply = payload.user_reply.strip()

        combined_input = f"""
{previous_input}

Additional Clarification:
{user_reply}
""".strip()

        graph = build_validation_graph()

        config = {
            "configurable": {
                "thread_id": f"validation-{user.id}-{session.id}-{uuid.uuid4().hex}"
            }
        }

        result = await graph.ainvoke(
            {
                "user_input": combined_input,
                "history": [],
                "attempts": 0,
                "messages": [],
                "reasoning": [],
                "retry_count": 0
            },
            config=config
        )

        ai = result.get("ai_response") or {}

        await ValidationSession.filter(
            id=session.id
        ).update(
            combined_input=combined_input,
            status=result.get("status"),
            ai_response=ai,
            is_completed=(result.get("status") == "valid"),
        )

        updated_session = await ValidationSession.get(id=session.id)

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="continue_prompt_request",
            message="Session updated after clarification",
            metadata={
                "session_id": updated_session.id,
                "status": updated_session.status,
                "combined_input": updated_session.combined_input
            },
        )

        return {
            "session_id": updated_session.id,
            "status": updated_session.status,
            "message": ai.get("message"),
            "combined_input": updated_session.combined_input,
        }

    except HTTPException:
        raise

    except Exception:

        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="continue_prompt_request",
            message="Continue validation crashed",
            metadata={
                "user_id": user.id if user else None
            },
            stack_trace=traceback.format_exc(),
        )

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )