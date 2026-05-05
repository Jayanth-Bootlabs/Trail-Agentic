import traceback
from fastapi import HTTPException
from models.validation_model import ValidationSession
from graph.builder import build_validation_graph
from utils.logger import log_event
from services.validation_rules import run_rule_validation

SERVICE_NAME = "validation_service"


async def validate_prompt_request(payload, user):
    try:
        user_input = payload.user_input

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="validate_prompt_request",
            message="Starting prompt validation",
            metadata={"user_id": user.id, "user_input": user_input},
        )

        rule_result = run_rule_validation(user_input)

        if rule_result:
            ai = rule_result
            
        else:
            graph = build_validation_graph()
            result = await graph.ainvoke({"user_input": user_input})
            ai = result["ai_response"]
            ai["source"] = "llm"

        session = await ValidationSession.create(
            user=user,
            user_input=user_input,
            combined_input=user_input,
            status=ai["status"],
            ai_response=ai,
            is_completed=(ai["status"] == "valid"),
        )

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="validate_prompt_request",
            message="Validation session created",
            metadata={"session_id": session.id, "status": ai["status"]},
        )

        return {
            "session_id": session.id,
            "status": ai["status"],
            "message": ai.get("message"),
        }

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="validate_prompt_request",
            message="Validation crashed",
            stack_trace=traceback.format_exc(),
        )
        raise


async def continue_prompt_request(payload, user):
    try:
        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="continue_prompt_request",
            message="Continuing validation",
            metadata={"user_id": user.id, "session_id": payload.session_id},
        )

        session = await ValidationSession.get_or_none(
            id=payload.session_id,
            user=user
        )

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        graph = build_validation_graph()
        result = await graph.ainvoke({"user_input": payload.user_reply})
        ai = result["ai_response"]

        session.combined_input = payload.user_reply
        session.status = ai["status"]
        session.ai_response = ai
        session.is_completed = ai["status"] == "valid"

        await session.save()

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="continue_prompt_request",
            message="Session updated after user reply",
            metadata={"session_id": session.id, "status": ai["status"]},
        )

        return {
            "session_id": session.id,
            "status": ai["status"],
        }

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="continue_prompt_request",
            message="Continue validation crashed",
            stack_trace=traceback.format_exc(),
        )
        raise