import traceback
from crewai import Crew
from models.requirements_gathering_model import RequirementSession
from models.code_generator_model import CodeSession
from utils.logger import log_event
from utils.helper import clean_ai_response

from tasks.code_task import get_code_task
from agents.code_agent import code_agent

SERVICE_NAME = "code_service"

async def generate_code_from_requirement(requirement_id: int):

    try:
        requirement = await RequirementSession.get(id=requirement_id)

        if not requirement:
            raise ValueError("Requirement not found")

        if requirement.status != "COMPLETED":
            raise ValueError("Requirement not ready for code generation")

        requirement_spec = requirement.requirement_spec

        code_record = await CodeSession.create(
            requirement_session=requirement,
            generated_code={},
            status="RUNNING"
        )

        task = get_code_task(requirement_spec)

        crew = Crew(
            agents=[code_agent],
            tasks=[task],
            verbose=True
        )

        crew_output = crew.kickoff()

        raw_output = crew_output.raw if hasattr(crew_output, "raw") else str(crew_output)

        structured_code = clean_ai_response(raw_output)

        if not structured_code:
            structured_code = raw_output

        code_record.generated_code = structured_code
        code_record.status = "COMPLETED"
        await code_record.save()

        return {
            "requirement_id": requirement_id,
            "code_session_id": code_record.id,
            "generated_code": structured_code
        }

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="generate_code_from_requirement",
            message="Code generation failed",
            stack_trace=traceback.format_exc(),
        )
        raise