import traceback
from fastapi import APIRouter, HTTPException
from schemas.requirements_schema import RequirementsRequest
from services.requirements_service import run_requirements_service
from utils.logger import log_event
from utils.response import format_response

router = APIRouter(tags=["Requirements"])

SERVICE_NAME = "requirements_routes"

@router.post("/generate_requirements")
async def generate_requirements(payload: RequirementsRequest):
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="generate_requirements",
        message="Requirements API called",
        metadata={"prompt_session_id": payload.prompt_session_id},
    )

    try:
        data = await run_requirements_service(payload)

        return format_response(
            data=data,
            message="Requirements generated successfully",
            status_code=200,
        )

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="generate_requirements",
            message="Failed to generate requirements",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")