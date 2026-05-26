import traceback

from fastapi import APIRouter, HTTPException, Request

from schemas.validation_schema import (
    ValidateRequest,
    ContinueRequest
)

from services.validation_service import (
    validate_prompt_request,
    continue_prompt_request
)

from utils.logger import log_event
from utils.response import format_response


router = APIRouter(tags=["Validation"])

SERVICE_NAME = "validation_routes"


@router.post("/validate_request")
async def validate_request(
    request: Request,
    payload: ValidateRequest
):

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="validate_request",
        message="Validate request API called",
        metadata={
            "user_id": request.state.user.id,
            "user_input": payload.user_input,
        },
    )

    try:

        data = await validate_prompt_request(
            payload=payload,
            user=request.state.user
        )

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

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.post("/continue_request")
async def continue_request(
    request: Request,
    payload: ContinueRequest
):

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="continue_request",
        message="Continue request API called",
        metadata={
            "user_id": request.state.user.id,
            "session_id": payload.session_id,
            "user_reply": payload.user_reply,
        },
    )

    try:

        data = await continue_prompt_request(
            payload=payload,
            user=request.state.user
        )

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
            metadata={
                "session_id": payload.session_id
            },
            stack_trace=traceback.format_exc(),
        )

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )