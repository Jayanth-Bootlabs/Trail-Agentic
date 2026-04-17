import traceback
from fastapi import APIRouter

from schemas.code_schema import CodeRequest
from services.code_service import generate_code_from_requirement
from utils.logger import log_event
from utils.response import format_response

router = APIRouter(tags=["Code Generator"])

SERVICE_NAME = "code_routes"


@router.post("/generate_code")
async def generate_code(payload: CodeRequest):

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="generate_code",
        message="Code generation API called",
    )

    try:
        result = await generate_code_from_requirement(payload.requirement_id)

        return format_response(
            data=result,
            message="Code generated successfully",
            status_code=200,
        )

    except ValueError as ve:
        return format_response(
            data={},
            message=str(ve),
            status_code=400,
        )

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="generate_code",
            message="Unexpected error",
            stack_trace=traceback.format_exc(),
        )

        return format_response(
            data={},
            message="Internal server error",
            status_code=500,
        )