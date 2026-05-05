import traceback
from fastapi import APIRouter, HTTPException
from schemas.insights_schema import GenerateInsightsRequest
from services.insights_service import generate_insights_service,get_insights_service

from utils.logger import log_event
from utils.response import format_response

router = APIRouter(tags=["Insights"])

SERVICE_NAME = "insights_routes"


@router.post("/generate-insights")
async def generate_insights(payload: GenerateInsightsRequest):
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="generate_insights",
        message="Generate insights API called",
        metadata={
    "user_id": payload.user_id,
    "session_id": payload.session_id
},
    )

    try:
        data = await generate_insights_service(payload)
        

        return format_response(
            data=data,
            message="Insights generated successfully",
            status_code=201,
        )

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="generate_insights",
            message="Insights generation failed",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/get-insights")
async def get_insights(user_id: int, session_id: int):
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="get_insights",
        message="Get insights API called",
        metadata={"user_id": user_id, "session_id": session_id},
    )

    try:
        data = await get_insights_service(user_id, session_id)

        return format_response(
            data=data,
            message="Insights fetched successfully",
            status_code=200,
        )

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="get_insights",
            message="Get insights failed",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")