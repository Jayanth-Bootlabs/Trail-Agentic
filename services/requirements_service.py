import traceback
from fastapi import HTTPException
from models.prompt_validator_model import PromptSession
from models.requirements_gathering_model import RequirementSession
from utils.logger import log_event
from utils.helper import clean_ai_response
from graph.graph_builder import build_requirements_graph

SERVICE_NAME = "requirements_service"


async def run_requirements_service(payload):
    try:
        prompt_session_id = payload.prompt_session_id

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="run_requirements_service",
            message="Fetching validated prompt",
            metadata={"prompt_session_id": prompt_session_id},
        )

        prompt_session = await PromptSession.filter(
            id=prompt_session_id
        ).first()

        if not prompt_session:
            raise HTTPException(status_code=404, detail="Prompt session not found")

        if not prompt_session.is_completed:
            raise HTTPException(
                status_code=400,
                detail="Prompt is not validated yet"
            )

        user_input = prompt_session.user_input

        graph = build_requirements_graph()

        state = {
            "user_input": user_input,
        }

        result = await graph.ainvoke(state)

        raw_output = result.get("ai_response")

        if not raw_output:
            raise ValueError("Empty response from LLM")

        requirement_output = clean_ai_response(raw_output)

        if not isinstance(requirement_output, dict):
            raise HTTPException(
                status_code=500,
                detail="Invalid requirements format from AI"
            )

        requirement_session = await RequirementSession.create(
            prompt_session=prompt_session,
            requirement_spec=requirement_output,
            is_completed=True
        )

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="run_requirements_service",
            message="Requirements stored successfully",
            metadata={"requirement_session_id": requirement_session.id},
        )

        return {
            "requirement_session_id": requirement_session.id,
            "data": requirement_output
        }

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="run_requirements_service",
            message="Requirements generation failed",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")