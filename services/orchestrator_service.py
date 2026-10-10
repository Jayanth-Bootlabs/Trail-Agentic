import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import HTTPException

from models.pipeline_run_model import PipelineRun, PipelineStep
from models.validation_model import ValidationSession
from models.requirements_model import RequirementSession
from models.code_model import GeneratedCode
from models.unit_tests_model import UnitTests
from models.insights_model import Insights
from models.documentation_model import Documentation

from schemas.validation_schema import ValidateRequest, ContinueRequest
from schemas.requirements_schema import StartRequirementRequest
from schemas.code_schema import CodeGenerationRequest
from schemas.unit_test_schema import UnitTestRequest
from schemas.insights_schema import GenerateInsightsRequest
from schemas.documentation_schema import GenerateDocumentationRequest

from services.validation_service import validate_prompt_request, continue_prompt_request
from services.requirements_service import start_requirements_request
from services.code_service import generate_code_service
from services.unit_test_service import generate_unit_tests_service
from services.insights_service import generate_insights_service
from services.documentation_service import generate_documentation_service

from utils.logger import log_event, reset_pipeline_context, set_pipeline_context
from utils.metrics import (
    PIPELINE_ACTIVE_RUNS,
    PIPELINE_CLARIFICATIONS,
    PIPELINE_RUNS,
    PIPELINE_STAGE_DURATION,
    PIPELINE_STAGE_FAILURES,
)


# This module coordinates the existing agent services. It does not contain their
# generation logic; it starts them in order, passes artifact IDs between them,
# and saves enough progress to report or resume a pipeline.
SERVICE_NAME = "orchestrator_service"


# Return a timezone-aware UTC timestamp for stage start and finish fields.
def _now():
    return datetime.now(timezone.utc)


# A run status describes the outcome of the whole pipeline. For example, the
# run can be awaiting clarification even though validation is the only step
# that has executed so far. This status cannot be inferred from one step alone.

RUNNING = "running"

AWAITING_CLARIFICATION = "awaiting_clarification"

COMPLETED = "completed"

FAILED = "failed"

REJECTED = "rejected"


# A step status describes one stage/agent in the pipeline. Keeping these
# separate from run status lets us show which stage failed and preserve earlier
# completed stages when retrying. A step is not "rejected": rejection is a
# pipeline outcome caused by validation, so the run is REJECTED and that step
# is marked STEP_FAILED with the rejection message. Likewise, clarification is
# a run-level pause; the validation step records the question/session and the
# run becomes AWAITING_CLARIFICATION. Combining the two status fields would
# lose either the overall outcome or per-stage progress.

STEP_PENDING = "pending"

STEP_RUNNING = "running"

STEP_COMPLETED = "completed"

STEP_FAILED = "failed"


# STAGES is the execution sequence. ARTIFACT_FIELD maps each stage to the
# PipelineRun field where its output ID is saved for later stages and API reads.

STAGES = [
    "validation",
    "requirements",
    "code",
    "unit_test",
    "insights",
    "documentation",
]

ARTIFACT_FIELD = {
    "validation": "validation_session_id",
    "requirements": "requirement_session_id",
    "code": "code_id",
    "unit_test": "unit_test_id",
    "insights": "insight_id",
    "documentation": "doc_id",
}


# These exceptions are deliberate control-flow outcomes from a stage, rather
# than unexpected crashes: the worker handles clarification and rejection in
# their own branches and updates run/step records accordingly.

# Carries the question to show the user and, when available, the validation
# session ID needed to continue validation after the user replies.
class ClarificationNeeded(Exception):
    def __init__(self, question: str, artifact_id: int | None = None):
        self.question = question
        self.artifact_id = artifact_id
        super().__init__(question)


# Carries the validation rejection reason so the worker can mark the run as
# rejected and expose the reason in its status.
class RequestRejected(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


# Stage handlers adapt the shared run record to the existing agent services.

# Run the validation service for new input, or continue its existing session
# when the user has replied to a clarification. Return the session ID on
# success; raise a control-flow exception when validation pauses or rejects.
async def _stage_validation(run: PipelineRun, user) -> int:
    if run.pending_reply:
        data = await continue_prompt_request(
            payload=ContinueRequest(
                session_id=run.validation_session_id,
                user_reply=run.pending_reply,
            ),
            user=user,
        )

        run.pending_reply = None
        run.combined_input = data.get("combined_input")
        await run.save()
    else:
        user_input = run.combined_input or run.user_input

        data = await validate_prompt_request(
            payload=ValidateRequest(user_input=user_input),
            user=user,
        )

    status = data.get("status")

    if status == "valid":
        return data.get("session_id")

    if status == "clarify":
        raise ClarificationNeeded(
            data.get("message") or "More information is required",
            artifact_id=data.get("session_id"),
        )

    raise RequestRejected(data.get("message") or "Request rejected")


@dataclass(frozen=True)
class ArtifactStage:
    """Configuration for one stage that creates a persisted artifact.

    The fields describe how to find its input on the run, build the service
    request, check for an already completed result, and read the output ID.
    """
    run_field: str
    request_field: str
    relation_field: str
    model: type
    service: object
    request: object
    response_field: str
    label: str
    needs_user: bool = False


# Keep the artifact stages declarative: each entry connects an existing service
# to its input schema, database model, and artifact ID fields. This avoids
# repeating nearly identical orchestration code for each agent.
ARTIFACT_STAGES = {
    "requirements": ArtifactStage(
        "validation_session_id", "validation_session_id", "validation_session_id", RequirementSession,
        start_requirements_request, StartRequirementRequest, "requirement_session_id",
        "requirement session", True,
    ),
    "code": ArtifactStage(
        "requirement_session_id", "requirements_id", "requirement_id", GeneratedCode,
        generate_code_service, CodeGenerationRequest, "code_id", "generated code",
    ),
    "unit_test": ArtifactStage(
        "code_id", "code_id", "code_id", UnitTests, generate_unit_tests_service,
        UnitTestRequest, "unit_test_id", "unit tests",
    ),
    "insights": ArtifactStage(
        "unit_test_id", "unit_test_id", "tests_id", Insights, generate_insights_service,
        GenerateInsightsRequest, "insight_id", "insights",
    ),
    "documentation": ArtifactStage(
        "insight_id", "insights_id", "insights_id", Documentation, generate_documentation_service,
        GenerateDocumentationRequest, "doc_id", "documentation",
    ),
}


# Run one configured artifact-producing service. Reuse a completed artifact if
# one already exists, which prevents duplicate work when a run resumes or two
# requests race to create the same result.
async def _run_artifact_stage(stage: str, run: PipelineRun, user) -> int:
    spec = ARTIFACT_STAGES[stage]
    source_id = getattr(run, spec.run_field)
    if not source_id:
        raise Exception(f"{stage} stage reached without its required input")

    filters = {spec.relation_field: source_id, "is_completed": True}
    existing = await spec.model.get_or_none(**filters)
    if existing:
        return existing.id

    request = spec.request(**{spec.request_field: source_id})
    try:
        if spec.needs_user:
            data = await spec.service(payload=request, user=user)
        else:
            data = await spec.service(payload=request)
    except HTTPException as exc:
        if exc.status_code != 409:
            raise
        existing = await spec.model.get_or_none(**filters)
        if not existing:
            raise
        return existing.id

    return data.get(spec.response_field)


# Dispatch table used by execute_run. The default argument captures the current
# stage in each lambda so every handler calls the service for its own stage.
STAGE_HANDLERS = {
    "validation": _stage_validation,
    **{stage: (lambda run, user, stage=stage: _run_artifact_stage(stage, run, user))
       for stage in ARTIFACT_STAGES},
}


# Services can return an ID for an incomplete artifact when generated output
# was unusable. Verify persistence and completion here so the next stage does
# not fail later with a confusing missing-input error.

# Confirm that a stage produced a completed database record before continuing.
async def _verify_artifact(stage: str, artifact_id: int) -> int:
    model = ValidationSession if stage == "validation" else ARTIFACT_STAGES[stage].model
    label = "validation session" if stage == "validation" else ARTIFACT_STAGES[stage].label
    record = await model.get_or_none(id=artifact_id)

    if not record:
        raise Exception(f"{label.capitalize()} was not persisted")
    if not record.is_completed:
        if stage == "code":
            raise Exception(
                "Code generation returned an empty or invalid payload — "
                "the source_code map was empty so the record was stored incomplete"
            )
        if stage == "validation":
            raise Exception("Validation session was produced but never marked valid")
        raise Exception(f"{label.capitalize()} was produced but marked incomplete")
    return artifact_id


# Background worker: executes the ordered stages, persists progress, and
# translates stage outcomes into run-level outcomes. Completed steps are skipped
# so a restart can continue from the first unfinished stage.

# Execute one run in the background. Step state records the result of each
# individual stage; run state records whether the entire pipeline is active,
# paused, rejected, failed, or complete. Metrics and logs are updated as work
# progresses, and the active-run gauge is always decremented on exit.
async def execute_run(run_id: int):
    active = False
    context_token = None

    try:
        run = await PipelineRun.get_or_none(id=run_id)

        if not run:
            log_event(
                level="ERROR",
                service=SERVICE_NAME,
                function="execute_run",
                message="Pipeline run not found",
                metadata={"run_id": run_id},
            )
            return

        if run.status in (AWAITING_CLARIFICATION, COMPLETED, REJECTED):
            log_event(
                level="WARNING",
                service=SERVICE_NAME,
                function="execute_run",
                message="Run is not executable in its current status",
                metadata={"run_id": run_id, "status": run.status},
            )
            return

        user = await run.user

        if not user:
            raise Exception("Pipeline run has no associated user")

        context_token = set_pipeline_context(run.id, run.user_input)

        run.status = RUNNING
        await run.save()

        PIPELINE_ACTIVE_RUNS.inc()
        active = True

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="execute_run",
            message="Pipeline run started",
            metadata={
                "run_id": run_id,
                "user_id": user.id,
            },
        )

        for stage in STAGES:

            step = await PipelineStep.get(run_id=run_id, stage=stage)

            if step.status == STEP_COMPLETED:
                log_event(
                    level="INFO",
                    service=SERVICE_NAME,
                    function="execute_run",
                    message="Skipping already completed stage",
                    metadata={"run_id": run_id, "stage": stage},
                )
                continue

            step.status = STEP_RUNNING
            step.attempt = (step.attempt or 0) + 1
            step.started_at = _now()
            await step.save()

            log_event(
                level="INFO",
                service=SERVICE_NAME,
                function="execute_run",
                message="Stage started",
                metadata={
                    "run_id": run_id,
                    "stage": stage,
                    "attempt": step.attempt,
                },
            )

            handler = STAGE_HANDLERS[stage]
            stage_started_at = time.perf_counter()

            try:
                artifact_id = await handler(run, user)
                artifact_id = await _verify_artifact(stage, artifact_id)
            except ClarificationNeeded as pause:
                # The validation attempt has finished for now, so its step is
                # recorded as completed and the whole run is paused. When the
                # user replies, clarify_pipeline resets this step to pending.
                step.status = STEP_COMPLETED
                step.artifact_id = pause.artifact_id
                step.finished_at = _now()
                await step.save()

                if pause.artifact_id is not None:
                    setattr(run, ARTIFACT_FIELD[stage], pause.artifact_id)

                run.status = AWAITING_CLARIFICATION
                run.clarification_question = pause.question
                await run.save()

                log_event(
                    level="INFO",
                    service=SERVICE_NAME,
                    function="execute_run",
                    message="Run paused awaiting clarification",
                    metadata={
                        "run_id": run_id,
                        "stage": stage,
                        "question": pause.question,
                        "artifact_id": pause.artifact_id,
                    },
                )

                PIPELINE_STAGE_DURATION.labels(stage=stage).observe(
                    time.perf_counter() - stage_started_at
                )
                PIPELINE_RUNS.labels(status=AWAITING_CLARIFICATION).inc()

                return

            except RequestRejected as rejected:

                step.status = STEP_FAILED
                step.error = rejected.message
                step.finished_at = _now()
                await step.save()

                run.status = REJECTED
                run.clarification_question = rejected.message
                await run.save()

                log_event(
                    level="INFO",
                    service=SERVICE_NAME,
                    function="execute_run",
                    message="Run rejected by validation agent",
                    metadata={
                        "run_id": run_id,
                        "stage": stage,
                        "message": rejected.message,
                    },
                )

                PIPELINE_STAGE_DURATION.labels(stage=stage).observe(
                    time.perf_counter() - stage_started_at
                )
                PIPELINE_STAGE_FAILURES.labels(stage=stage).inc()
                PIPELINE_RUNS.labels(status=REJECTED).inc()

                return

            except Exception:

                step.status = STEP_FAILED
                step.error = traceback.format_exc()[-4000:]
                step.finished_at = _now()
                await step.save()

                run.status = FAILED
                await run.save()

                log_event(
                    level="ERROR",
                    service=SERVICE_NAME,
                    function="execute_run",
                    message="Stage failed",
                    stack_trace=traceback.format_exc(),
                    metadata={
                        "run_id": run_id,
                        "stage": stage,
                    },
                )

                PIPELINE_STAGE_DURATION.labels(stage=stage).observe(
                    time.perf_counter() - stage_started_at
                )
                PIPELINE_STAGE_FAILURES.labels(stage=stage).inc()
                PIPELINE_RUNS.labels(status=FAILED).inc()

                return

            if artifact_id is not None:
                setattr(run, ARTIFACT_FIELD[stage], artifact_id)

            step.status = STEP_COMPLETED
            step.artifact_id = artifact_id
            step.finished_at = _now()
            await step.save()

            await run.save()

            log_event(
                level="INFO",
                service=SERVICE_NAME,
                function="execute_run",
                message="Stage completed",
                metadata={
                    "run_id": run_id,
                    "stage": stage,
                    "artifact_id": artifact_id,
                },
            )

            PIPELINE_STAGE_DURATION.labels(stage=stage).observe(
                time.perf_counter() - stage_started_at
            )

        run.status = COMPLETED
        await run.save()

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="execute_run",
            message="Pipeline run completed",
            metadata={"run_id": run_id},
        )

        PIPELINE_RUNS.labels(status=COMPLETED).inc()

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="execute_run",
            message="Pipeline worker crashed",
            stack_trace=traceback.format_exc(),
            metadata={"run_id": run_id},
        )

        if active:
            PIPELINE_RUNS.labels(status=FAILED).inc()

    finally:
        if context_token is not None:
            reset_pipeline_context(context_token)
        if active:
            PIPELINE_ACTIVE_RUNS.dec()


# Public operations called by API routes. These create, resume, restart, or
# report on persisted pipeline runs; the routes schedule execute_run afterward.

# Create the overall run record and one pending step record per stage. The
# worker will update these records as it executes the pipeline.
async def start_pipeline(user_input: str, user):
    run = await PipelineRun.create(
        user=user,
        user_input=user_input,
        status=RUNNING,
    )

    for stage in STAGES:
        await PipelineStep.create(
            run=run,
            stage=stage,
            status=STEP_PENDING,
        )

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="start_pipeline",
        message="Pipeline run created",
        metadata={
            "run_id": run.id,
            "user_id": user.id,
        },
    )

    return run


# Save the user's answer to a clarification pause, mark the overall run active,
# and reset validation so the worker can continue the existing validation
# session. Later completed stages are left untouched.
async def clarify_pipeline(run_id: int, user_reply: str, user):
    run = await PipelineRun.get_or_none(id=run_id, user=user)

    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")

    if run.status != AWAITING_CLARIFICATION:
        raise HTTPException(
            status_code=400,
            detail="This run is not awaiting clarification",
        )

    run.pending_reply = user_reply
    run.clarification_question = None
    run.status = RUNNING
    await run.save()

    await PipelineStep.filter(
        run_id=run_id,
        stage="validation",
    ).update(
        status=STEP_PENDING,
        error=None,
        started_at=None,
        finished_at=None,
    )

    PIPELINE_CLARIFICATIONS.inc()

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="clarify_pipeline",
        message="Clarification received, resuming run",
        metadata={
            "run_id": run_id,
            "user_id": user.id,
            "validation_session_id": run.validation_session_id,
        },
    )

    return run


# Prepare a failed run for another worker attempt. Completed stages remain
# complete; unfinished stages are reset so execute_run can resume at the first
# one that still needs work.
async def restart_pipeline(run_id: int, user):
    run = await PipelineRun.get_or_none(id=run_id, user=user)

    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")

    if run.status in (AWAITING_CLARIFICATION, COMPLETED, REJECTED):
        raise HTTPException(
            status_code=400,
            detail=f"A {run.status} run cannot be restarted",
        )

    await PipelineStep.filter(run_id=run_id).exclude(
        status=STEP_COMPLETED
    ).update(
        status=STEP_PENDING,
        error=None,
        started_at=None,
        finished_at=None,
    )

    run.status = RUNNING
    await run.save()

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="restart_pipeline",
        message="Pipeline run restarted from failure",
        metadata={"run_id": run_id, "user_id": user.id},
    )

    return run


# Return the overall run outcome together with every stage's status, attempt,
# artifact, error, and timestamps. Ownership is checked before exposing details.
async def get_run_status(run_id: int, user):
    run = await PipelineRun.get_or_none(id=run_id, user=user)

    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")

    steps = await PipelineStep.filter(run_id=run_id).order_by("id")

    return {
        "run_id": run.id,
        "status": run.status,
        "user_input": run.user_input,
        "combined_input": run.combined_input,
        "clarification_question": run.clarification_question,
        "awaiting_clarification": run.status == AWAITING_CLARIFICATION,
        "artifacts": {
            "validation_session_id": run.validation_session_id,
            "requirement_session_id": run.requirement_session_id,
            "code_id": run.code_id,
            "unit_test_id": run.unit_test_id,
            "insight_id": run.insight_id,
            "doc_id": run.doc_id,
        },
        "steps": [
            {
                "stage": step.stage,
                "status": step.status,
                "attempt": step.attempt,
                "artifact_id": step.artifact_id,
                "error": step.error,
                "started_at": str(step.started_at) if step.started_at else None,
                "finished_at": str(step.finished_at) if step.finished_at else None,
            }
            for step in steps
        ],
        "created_at": str(run.created_at) if run.created_at else None,
        "updated_at": str(run.updated_at) if run.updated_at else None,
    }
