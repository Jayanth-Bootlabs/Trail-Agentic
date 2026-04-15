import traceback
from fastapi import APIRouter, Request
from schemas.validation_schema import PromptRequest
from services.validation_service import validate_prompt_service
from utils.logger import log_event
from utils.response import format_response

router = APIRouter(tags=["Validation"])

SERVICE_NAME = "validation_routes"


@router.post("/validate_prompt")
async def validate_prompt(payload: PromptRequest, request: Request):

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="validate_prompt",
        message="Validation API called",
    )

    try:
        data = await validate_prompt_service(payload, request)

        return format_response(
            data=data,
            message="Validation response generated",
            status_code=200,
        )

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="validate_prompt",
            message="Validation failed",
            stack_trace=traceback.format_exc(),
        )
        raise