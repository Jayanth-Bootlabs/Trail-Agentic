import traceback
from fastapi import HTTPException
from builder.requirements_builder import build_requirements_graph
from schemas.requirements_schema import StartRequirementRequest
from models.validation_model import ValidationSession
from models.requirements_model import RequirementSession
from utils.logger import log_event

SERVICE_NAME = "requirements_service"


async def start_requirements_request(payload: StartRequirementRequest, user):
    try:
        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="start_requirements_request",
            message="Starting requirements gathering",
            metadata={
                "validation_session_id": payload.validation_session_id,
                "user_id": user.id,
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

        user_input = validation.combined_input

        graph = build_requirements_graph()

        config = {
            "configurable": {
                "thread_id": f"requirements-{payload.validation_session_id}"
            }
        }

        result = await graph.ainvoke(
            {
                "user_input": user_input,
                "retry_count": 0
            },
            config=config
        )

        ai = result.get("requirements", {})

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="start_requirements_request",
            message="Requirements data from state",
            metadata={"ai_keys": list(ai.keys()) if ai else []},
        )

        session = await RequirementSession.create(
            validation_session=validation,
            user_input=user_input,
            status=result.get("status"),
            ai_response=ai,
            is_completed=(result.get("status") == "valid"),
        )

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="start_requirements_request",
            message="Requirements gathering completed",
            metadata={
                "requirement_session_id": session.id,
                "status": result.get("status"),
            },
        )

        return {
            "requirement_session_id": session.id,
            "status": result.get("status"),
            "message": ai.get("message", ""),
            "data": ai.get("data", {}),
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