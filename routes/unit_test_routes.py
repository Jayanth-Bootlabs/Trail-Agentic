import traceback
from fastapi import APIRouter, HTTPException
from schemas.unit_test_schema import UnitTestRequest
from services.unit_test_service import generate_unit_tests_service, get_unit_tests_service
from utils.logger import log_event
from utils.response import format_response

router = APIRouter(tags=["Unit Tests"])
SERVICE_NAME = "unit_tests_routes"


@router.post("/generate-unit-tests")
async def generate_unit_tests(payload: UnitTestRequest):
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="generate_unit_tests",
        message="Generate unit tests API called",
        metadata={"code_id": payload.code_id},
    )

    try:
        data = await generate_unit_tests_service(payload)

        return format_response(
            data=data,
            message="Unit tests generated successfully",
            status_code=201,
        )

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="generate_unit_tests",
            message="Unit tests generation failed",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/get-unit-tests")
async def get_unit_tests(unit_test_id: int):
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="get_unit_tests",
        message="Get unit tests API called",
        metadata={"unit_test_id": unit_test_id},
    )

    try:
        data = await get_unit_tests_service(unit_test_id)
        return format_response(data=data, message="Unit tests fetched successfully", status_code=200)

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR", 
            service=SERVICE_NAME, 
            function="get_unit_tests",
            message="Get unit tests failed", 
            stack_trace=traceback.format_exc()
            )
        raise HTTPException(status_code=500, detail="Internal server error")