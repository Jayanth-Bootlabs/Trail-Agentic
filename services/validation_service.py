import traceback
from models.prompt_session import PromptSession
from utils.logger import log_event
from crewai import Crew
from tasks.validation_task import get_validation_task
from agents.validation_agent import validation_agent
from fastapi import Request
from utils.helper import clean_ai_response

SERVICE_NAME = "validation_service"


async def validate_prompt_service(payload, request: Request):
    try:
        user_input = payload.input

        user = request.state.user
        if not user:
            raise ValueError("No user found in database")

        user_id = user.id

        # Create task
        task = get_validation_task(user_input)

        # Run crew
        crew = Crew(
            agents=[validation_agent],
            tasks=[task],
            verbose=True
        )

        crew_output = crew.kickoff()

        raw_output = crew_output.raw if hasattr(crew_output, "raw") else str(crew_output)

        # CLEAN + PARSE
        parsed_output = clean_ai_response(raw_output)

        is_completed = isinstance(parsed_output, dict)

        session = await PromptSession.create(
            user_id=user_id,
            user_input=user_input,
            ai_response=parsed_output,
            is_completed=is_completed
        )

        return {
            "session_id": session.id,
            "response": parsed_output,
            "is_completed": is_completed
        }

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="validate_prompt_service",
            message="Validation failed",
            stack_trace=traceback.format_exc(),
        )
        raise