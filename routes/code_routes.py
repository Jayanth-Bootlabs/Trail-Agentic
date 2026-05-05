import traceback
from fastapi import APIRouter, HTTPException, Request
from schemas.code_schema import CodeGenerationRequest
from services.code_service import generate_code_service
from utils.logger import log_event
from utils.response import format_response
from services.code_service import generate_code_service, get_generated_code_service

from schemas.code_schema import CodeGenerationRequest


router = APIRouter(tags=["Code Generation"])

SERVICE_NAME = "code_generation_routes"


@router.post("/generate-code")
async def generate_code(request: Request, payload: CodeGenerationRequest):
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="generate_code",
        message="Generate code API called",
        metadata={
            "user_id": request.state.user.id,
            "session_id": payload.session_id
        },
    )

    try:
        data = await generate_code_service(
            user_id=request.state.user.id,
            session_id=payload.session_id
        )

        return format_response(
            data=data,
            message="Code generated successfully",
            status_code=201,
        )

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="generate_code",
            message="Generate code failed",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/get-code")
async def get_code(request: Request, session_id: int):
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="get_code",
        message="Get code API called",
        metadata={
            "user_id": request.state.user.id,
            "session_id": session_id
        },
    )

    try:
        data = await get_generated_code_service(
            user_id=request.state.user.id,
            session_id=session_id
        )

        return format_response(
            data=data,
            message="Code fetched successfully",
            status_code=200,
        )

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="get_code",
            message="Get code failed",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")