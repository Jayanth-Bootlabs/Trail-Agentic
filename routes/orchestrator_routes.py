import traceback

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from schemas.orchestrator_schema import (
    StartPipelineRequest,
    ClarifyPipelineRequest,
)

from services.orchestrator_service import (
    start_pipeline,
    execute_run,
    clarify_pipeline,
    restart_pipeline,
    get_run_status,
)

from utils.logger import log_event
from utils.response import format_response


router = APIRouter(tags=["Orchestrator"])

SERVICE_NAME = "orchestrator_routes"


@router.post("/pipeline/run")
async def run_pipeline(
    request: Request,
    background_tasks: BackgroundTasks,
    payload: StartPipelineRequest,
):

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="run_pipeline",
        message="Start pipeline API called",
        metadata={
            "user_id": request.state.user.id,
        },
    )

    try:

        run = await start_pipeline(
            user_input=payload.user_input.strip(),
            user=request.state.user,
        )

        background_tasks.add_task(execute_run, run.id)

        return format_response(
            data={
                "run_id": run.id,
                "status": run.status,
            },
            message="Pipeline started",
            status_code=201,
        )

    except HTTPException:
        raise

    except Exception:

        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="run_pipeline",
            message="Start pipeline failed",
            stack_trace=traceback.format_exc(),
        )

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get("/pipeline/run/{run_id}")
async def pipeline_status(request: Request, run_id: int):

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="pipeline_status",
        message="Pipeline status API called",
        metadata={
            "user_id": request.state.user.id,
            "run_id": run_id,
        },
    )

    try:

        data = await get_run_status(
            run_id=run_id,
            user=request.state.user,
        )

        return format_response(
            data=data,
            message="Pipeline status retrieved successfully",
            status_code=200,
        )

    except HTTPException:
        raise

    except Exception:

        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="pipeline_status",
            message="Pipeline status failed",
            metadata={"run_id": run_id},
            stack_trace=traceback.format_exc(),
        )

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.post("/pipeline/run/{run_id}/clarify")
async def clarify_pipeline_request(
    request: Request,
    background_tasks: BackgroundTasks,
    run_id: int,
    payload: ClarifyPipelineRequest,
):

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="clarify_pipeline_request",
        message="Clarify pipeline API called",
        metadata={
            "user_id": request.state.user.id,
            "run_id": run_id,
        },
    )

    try:

        run = await clarify_pipeline(
            run_id=run_id,
            user_reply=payload.user_reply.strip(),
            user=request.state.user,
        )

        background_tasks.add_task(execute_run, run.id)

        return format_response(
            data={
                "run_id": run.id,
                "status": run.status,
            },
            message="Clarification accepted, pipeline resumed",
            status_code=200,
        )

    except HTTPException:
        raise

    except Exception:

        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="clarify_pipeline_request",
            message="Clarify pipeline failed",
            metadata={"run_id": run_id},
            stack_trace=traceback.format_exc(),
        )

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.post("/pipeline/run/{run_id}/restart")
async def restart_pipeline_request(
    request: Request,
    background_tasks: BackgroundTasks,
    run_id: int,
):

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="restart_pipeline_request",
        message="Restart pipeline API called",
        metadata={
            "user_id": request.state.user.id,
            "run_id": run_id,
        },
    )

    try:

        run = await restart_pipeline(
            run_id=run_id,
            user=request.state.user,
        )

        background_tasks.add_task(execute_run, run.id)

        return format_response(
            data={
                "run_id": run.id,
                "status": run.status,
            },
            message="Pipeline restarted",
            status_code=200,
        )

    except HTTPException:
        raise

    except Exception:

        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="restart_pipeline_request",
            message="Restart pipeline failed",
            metadata={"run_id": run_id},
            stack_trace=traceback.format_exc(),
        )

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )