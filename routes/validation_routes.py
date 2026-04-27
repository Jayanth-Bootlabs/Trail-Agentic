import traceback
from fastapi import APIRouter, HTTPException
from schemas.validation_schema import ValidateRequest, ContinueRequest
from services.validation_service import (
    validate_prompt_request,
    continue_prompt_request
)
from utils.logger import log_event
from utils.response import format_response

router = APIRouter(tags=["Validation"])

SERVICE_NAME = "validation_routes"


@router.post("/validate-request")
async def validate_request(payload: ValidateRequest):
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="validate_request",
        message="Validate prompt request API called",
        metadata={"user_input": payload.user_input},
    )

    try:
        data = await validate_prompt_request(payload)

        return format_response(
            data=data,
            message="Validation completed successfully",
            status_code=200,
        )

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="validate_request",
            message="Validate request failed",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/continue-request")
async def continue_request(payload: ContinueRequest):
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="continue_request",
        message="Continue prompt request API called",
        metadata={"session_id": payload.session_id},
    )

    try:
        data = await continue_prompt_request(payload)

        return format_response(
            data=data,
            message="Continue validation completed successfully",
            status_code=200,
        )

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="continue_request",
            message="Continue request failed",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")