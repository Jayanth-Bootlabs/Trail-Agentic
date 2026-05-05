import traceback
from graph.state import GraphState
from prompts.validation_prompt import get_validation_prompt
from utils.gemini_llm import llm
from utils.logger import log_event
from utils.helper import clean_ai_response
from prompts.requirements_prompt import get_requirements_prompt
from prompts.coding_prompt import get_coding_prompt

SERVICE_NAME = "validation_node"


async def validate_node(state: GraphState) -> GraphState:
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="validate_node",
        message="Validation node started",
        metadata={"user_input": state["user_input"]},
    )

    try:
        prompt = get_validation_prompt(state["user_input"])

        response = await llm.generate(prompt)

        parsed = clean_ai_response(response)

        if not parsed:
            log_event(
                level="WARNING",
                service=SERVICE_NAME,
                function="validate_node",
                message="Invalid JSON response from LLM",
                metadata={"raw_response": response},
            )

            parsed = {
                "status": "invalid",
                "message": "Invalid AI response"
            }

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="validate_node",
            message="Validation node completed",
            metadata={"status": parsed["status"]},
        )

        return {
            **state,
            "ai_response": parsed,
            "status": parsed["status"]
        }

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="validate_node",
            message="Validation node failed",
            stack_trace=traceback.format_exc(),
        )
        raise

async def requirements_node(state: GraphState) -> GraphState:
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="requirements_node",
        message="Requirements node started",
        metadata={"user_input": state["user_input"]},
    )

    try:
        prompt = get_requirements_prompt(state["user_input"])

        response = await llm.generate(prompt)

        parsed = clean_ai_response(response)

        if not parsed:
            parsed = {
                "status": "clarify",
                "message": "Please provide more details.",
                "data": {}
            }

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="requirements_node",
            message="Requirements node completed",
            metadata={"status": parsed["status"]},
        )

        return {
            **state,
            "ai_response": parsed,
            "status": parsed["status"]
        }

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="requirements_node",
            message="Requirements node failed",
            stack_trace=traceback.format_exc(),
        )
        raise

async def coding_node(state: GraphState) -> GraphState:
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="coding_node",
        message="Coding node started",
        metadata={"requirements": state["user_input"]},
    )

    try:
        prompt = get_coding_prompt(state["user_input"])

        response = await llm.generate(prompt)

        parsed = clean_ai_response(response)

        if not parsed:
            parsed = {
                "status": "partial",
                "message": "Invalid AI response",
                "code": {}
            }

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="coding_node",
            message="Coding node completed",
            metadata={"status": parsed["status"]},
        )

        return {
            **state,
            "ai_response": parsed,
            "status": parsed["status"]
        }

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="coding_node",
            message="Coding node failed",
            stack_trace=traceback.format_exc(),
        )
        raise