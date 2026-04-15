import traceback
import json
from fastapi import Request
from crewai import Crew
from models.prompt_validator_model import PromptSession
from utils.logger import log_event
from tasks.validation_task import get_validation_task
from agents.validation_agent import validation_agent
from utils.helper import clean_ai_response

SERVICE_NAME = "validation_service"


async def validate_prompt_service(payload, request: Request):
    try:
        user_input = payload.input

        user = request.state.user
        if not user:
            raise ValueError("No user found in database")

        task = get_validation_task(user_input)

        crew = Crew(
            agents=[validation_agent],
            tasks=[task],
            verbose=True
        )

        crew_output = crew.kickoff()
        raw_output = crew_output.raw if hasattr(crew_output, "raw") else str(crew_output)

        cleaned_output = clean_ai_response(raw_output)

        session = await PromptSession.create(
            user=user,
            user_input=user_input,
            ai_response=raw_output,
            is_completed=True
        )

        return {
            "session_id": session.id,
            "response": cleaned_output,
            "is_completed": True
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