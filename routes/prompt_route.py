import traceback
from fastapi import APIRouter, HTTPException, Request
from schemas.prompt_schema import PromptRequest
from services.prompt_service import run_prompt_service
from utils.logger import log_event
from utils.response import format_response

router = APIRouter(tags=["Prompt"])

SERVICE_NAME = "prompt_routes"


@router.post("/create_prompt")
async def create_prompt(payload: PromptRequest, request: Request):
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="create_prompt",
        message="Create prompt API called",
        metadata={},
    )

    try:
        data = await run_prompt_service(payload, request)

        return format_response(
            data=data,
            message="Prompt processed successfully",
            status_code=200,
        )

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="create_prompt",
            message="Failed to process prompt",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")