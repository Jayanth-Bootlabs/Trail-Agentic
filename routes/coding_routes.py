import traceback
from fastapi import APIRouter, HTTPException
from schemas.coding_schema import StartCodingRequest
from services.coding_service import (
    start_coding_request,
)
from utils.logger import log_event
from utils.response import format_response

router = APIRouter(tags=["Coding"])

SERVICE_NAME = "coding_routes"


@router.post("/start_coding")
async def start_coding(payload: StartCodingRequest):
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="start_coding",
        message="Coding API called",
        metadata={"requirement_session_id": payload.requirement_session_id},
    )

    try:
        data = await start_coding_request(payload)

        return format_response(
            data=data,
            message="Coding completed successfully",
            status_code=200,
        )

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="start_coding",
            message="Coding API failed",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")