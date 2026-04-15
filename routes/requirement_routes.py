import traceback
from fastapi import APIRouter
from schemas.requirement_schema import RequirementRequest
from services.requirement_service import generate_requirement_spec
from utils.logger import log_event
from utils.response import format_response

router = APIRouter(tags=["Requirement Generator"])

SERVICE_NAME = "requirement_routes"


@router.post("/generate_requirement")
async def generate_requirement(payload: RequirementRequest):

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="generate_requirement",
        message="Requirement API called",
    )

    try:
        result = await generate_requirement_spec(payload.session_id)

        return format_response(
            data=result,
            message="Requirement generated successfully",
            status_code=200,
        )

    except ValueError as ve:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="generate_requirement",
            message=str(ve),
            stack_trace=traceback.format_exc(),
        )

        return format_response(
            data={},
            message=str(ve),
            status_code=400,
        )

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="generate_requirement",
            message="Unexpected error",
            stack_trace=traceback.format_exc(),
        )

        return format_response(
            data={},
            message="Internal server error",
            status_code=500,
        )