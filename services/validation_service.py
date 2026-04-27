import traceback
from fastapi import HTTPException
from models.validation_model import ValidationSession
from graph.builder import build_validation_graph
from utils.logger import log_event
from services.validation_rules import run_rule_validation

SERVICE_NAME = "validation_service"

async def validate_prompt_request(payload):
    try:
        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="validate_prompt_request",
            message="Starting prompt validation",
            metadata={"user_input": payload.user_input},
        )

        user_input = payload.user_input

        # Step 1 Rule Engine
        rule_result = run_rule_validation(user_input)

        if rule_result:
            log_event(
                level="INFO",
                service=SERVICE_NAME,
                function="validate_prompt_request",
                message="Resolved by rule engine",
                metadata=rule_result,
            )

            session = await ValidationSession.create(
                user_input=user_input,
                combined_input=user_input,
                status=rule_result["status"],
                ai_response=rule_result,
                is_completed=(rule_result["status"] == "valid")
            )

            return {
                "session_id": session.id,
                **rule_result
            }

        # Step 2 LLM Validation
        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="validate_prompt_request",
            message="Escalating request to LLM",
            metadata={"user_input": user_input},
        )

        graph = build_validation_graph()

        result = await graph.ainvoke({
            "user_input": user_input
        })

        ai = result["ai_response"]
        ai["source"] = "llm"

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="validate_prompt_request",
            message="LLM validation completed",
            metadata=ai,
        )

        session = await ValidationSession.create(
            user_input=user_input,
            combined_input=user_input,
            status=ai["status"],
            ai_response=ai,
            is_completed=(ai["status"] == "valid")
        )

        return {
            "session_id": session.id,
            **ai
        }

    except Exception as e:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="validate_prompt_request",
            message="Prompt validation failed",
            metadata={
                "error": str(e),
                "user_input": getattr(payload, "user_input", None)
            },
        )

        return {
            "status": "error",
            "message": "Something went wrong while validating your request. Please try again."
        }


async def continue_prompt_request(payload):
    try:
        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="continue_prompt_request",
            message="Continuing prompt validation",
            metadata={"session_id": payload.session_id},
        )

        session = await ValidationSession.get(id=payload.session_id)

        graph = build_validation_graph()

        result = await graph.ainvoke({
            "user_input": payload.user_reply
        })

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
            message="Prompt validation continued successfully",
            metadata={
                "session_id": session.id,
                "status": ai["status"]
            },
        )

        return {
            "session_id": session.id,
            "status": ai["status"],
            "user_input": payload.user_reply
        }

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="continue_prompt_request",
            message="Continue prompt validation failed",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")