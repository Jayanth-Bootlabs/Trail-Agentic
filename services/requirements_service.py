import traceback
from fastapi import HTTPException
from models.validation_model import ValidationSession
from models.requirements_model import RequirementSession
from graph.builder import build_requirements_graph
from utils.logger import log_event

SERVICE_NAME = "requirements_service"


async def start_requirements_request(payload):
    try:
        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="start_requirements_request",
            message="Starting requirements gathering",
            metadata={
                "validation_session_id": payload.validation_session_id
            },
        )

        validation = await ValidationSession.filter(
            id=payload.validation_session_id
        ).first()

        if not validation:
            raise HTTPException(
                status_code=404,
                detail="Validation session not found"
            )

        if validation.status != "valid" or not validation.is_completed:
            raise HTTPException(
                status_code=400,
                detail="Validation is not completed successfully"
            )

        user_input = validation.combined_input or validation.user_input

        graph = build_requirements_graph()

        result = await graph.ainvoke({
            "user_input": user_input
        })

        ai = result["ai_response"]

        session = await RequirementSession.create(
            validation_session=validation,
            user_input=user_input,
            combined_input=user_input,
            status=ai["status"],
            ai_response=ai,
            is_completed=(ai["status"] == "completed")
        )

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="start_requirements_request",
            message="Requirements gathering completed",
            metadata={
                "requirement_session_id": session.id,
                "status": ai["status"]
            },
        )

        return {
            "requirement_session_id": session.id,
            "status": ai["status"],
            "message": ai["message"],
            "data": ai.get("data", {})
        }

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="start_requirements_request",
            message="Requirements start failed",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")


async def continue_requirements_request(payload):
    try:
        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="continue_requirements_request",
            message="Continuing requirements gathering",
            metadata={
                "requirement_session_id": payload.requirement_session_id
            },
        )

        session = await RequirementSession.get(
            id=payload.requirement_session_id
        )

        merged_input = (
            (session.combined_input or "") +
            " " +
            payload.user_reply
        )

        graph = build_requirements_graph()

        result = await graph.ainvoke({
            "user_input": merged_input
        })

        ai = result["ai_response"]

        session.combined_input = merged_input
        session.status = ai["status"]
        session.ai_response = ai
        session.is_completed = ai["status"] == "completed"

        await session.save()

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="continue_requirements_request",
            message="Requirements continue completed",
            metadata={
                "requirement_session_id": session.id,
                "status": ai["status"]
            },
        )

        return {
            "requirement_session_id": session.id,
            "status": ai["status"],
            "message": ai["message"],
            "data": ai.get("data", {})
        }

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="continue_requirements_request",
            message="Requirements continue failed",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")