import traceback
from fastapi import APIRouter, HTTPException, Request
from schemas.code_schema import CodeGenerationRequest
from services.code_service import generate_code_service, get_generated_code_service
from utils.logger import log_event
from utils.response import format_response

router = APIRouter(tags=["Coding"])
SERVICE_NAME = "code_routes"


@router.post("/generate_code")
async def generate_code(request: Request,payload: CodeGenerationRequest):
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="generate_code",
        message="Generate code API called",
        metadata={
            "user_id": request.state.user.id,
            "requirements_id": payload.requirements_id,
        },
    )

    try:
        data = await generate_code_service(payload=payload)

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


@router.get("/get_code")
async def get_code(request: Request,code_id: int):
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="get_code",
        message="Fetch code API called",
        metadata={
            "user_id": request.state.user.id,
            "code_id": code_id,
        },
    )

    try:
        data = await get_generated_code_service(code_id=code_id)

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
            message="Fetch code failed",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")