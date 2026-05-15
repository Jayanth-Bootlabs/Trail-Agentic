import traceback
from fastapi import APIRouter, HTTPException, Request
from schemas.requirements_schema import StartRequirementRequest
from services.requirements_service import start_requirements_request
from utils.logger import log_event
from utils.response import format_response

router = APIRouter(tags=["Requirements"])

SERVICE_NAME = "requirements_routes"


@router.post("/generate_requirements")
async def start_requirements(
    request: Request,
    payload: StartRequirementRequest
):
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="start_requirements",
        message="Requirements start API called",
        metadata={
            "user_id": request.state.user.id,
            "validation_session_id": payload.validation_session_id,
        },
    )

    try:
        data = await start_requirements_request(
            payload=payload,
            user=request.state.user
        )

        return format_response(
            data=data,
            message="Requirements generated successfully",
            status_code=201,
        )

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="start_requirements",
            message="Requirements generation failed",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")