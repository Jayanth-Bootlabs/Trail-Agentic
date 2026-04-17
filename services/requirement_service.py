import traceback
from crewai import Crew
from models.prompt_validator_model import PromptSession
from models.requirements_gathering_model import RequirementSession
from utils.logger import log_event
from tasks.requirement_task import get_requirement_task
from agents.requirement_agent import requirement_agent
from utils.helper import clean_ai_response

SERVICE_NAME = "requirement_service"


async def generate_requirement_spec(session_id: int):
    try:
        session = await PromptSession.get(id=session_id)

        if not session:
            raise ValueError("Session not found")

        if not session.is_completed:
            raise ValueError("Validation not completed yet")

        validated_output = clean_ai_response(session.ai_response)

        if not validated_output or not isinstance(validated_output, dict):
            raise ValueError("Invalid validation JSON from session")

        requirement_record = await RequirementSession.create(
            prompt_session=session,
            validated_output=validated_output,
            requirement_spec="PENDING_GENERATION",
            status="RUNNING"
        )

        task = get_requirement_task(validated_output)

        crew = Crew(
            agents=[requirement_agent],
            tasks=[task],
            verbose=True
        )

        crew_output = crew.kickoff()

        raw_output = crew_output.raw if hasattr(crew_output, "raw") else str(crew_output)

        structured_spec = clean_ai_response(raw_output)

        if not structured_spec:
            structured_spec = raw_output

        requirement_record.requirement_spec = structured_spec
        requirement_record.status = "COMPLETED"
        await requirement_record.save()

        return {
            "session_id": session_id,
            "requirement_id": requirement_record.id,
            "requirement_spec": structured_spec
        }

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="generate_requirement_spec",
            message="Requirement generation failed",
            stack_trace=traceback.format_exc(),
        )
        if "requirement_record" in locals():
            requirement_record.status = "FAILED"
            await requirement_record.save()

        raise