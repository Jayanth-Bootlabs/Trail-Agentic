import traceback
from fastapi import APIRouter, HTTPException, Request
from schemas.documentation_schema import GenerateDocumentationRequest
from services.documentation_service import generate_documentation_service, get_documentation_service
from utils.logger import log_event
from utils.response import format_response

router = APIRouter(tags=["Documentation"])
SERVICE_NAME = "documentation_routes"


@router.post("/generate_documentation")
async def generate_documentation(request: Request,payload: GenerateDocumentationRequest):
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="generate_documentation",
        message="Generate documentation API called",
        metadata={
            "user_id": request.state.user.id,
            "insights_id": payload.insights_id,
        },
    )

    try:
        data = await generate_documentation_service(payload=payload)

        return format_response(
            data=data,
            message="Documentation generated successfully",
            status_code=201,
        )

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="generate_documentation",
            message="Documentation generation failed",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/get_documentation")
async def get_documentation(request: Request,documentation_id: int):
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="get_documentation",
        message="Get documentation API called",
        metadata={
            "user_id": request.state.user.id,
            "documentation_id": documentation_id,
        },
    )

    try:
        data = await get_documentation_service(documentation_id=documentation_id)

        return format_response(
            data=data,
            message="Documentation fetched successfully",
            status_code=200,
        )

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="get_documentation",
            message="Get documentation failed",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")