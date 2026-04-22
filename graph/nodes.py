import traceback
from graph.state import GraphState
from utils.gemini_llm import llm
from utils.logger import log_event
from prompts.validation_prompt import get_validation_prompt

SERVICE_NAME = "graph_nodes"


async def start_node(state: GraphState) -> GraphState:
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="start_node",
        message="Graph execution started",
    )

    return {
        **state,
        "status": "processing"
    }


async def llm_node(state: GraphState) -> GraphState:
    try:
        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="llm_node",
            message="LLM node execution started",
        )

        prompt = get_validation_prompt(state["user_input"])

        response = await llm.generate(prompt)

        clean_response = response.strip()

        if clean_response.startswith("```json"):
            clean_response = clean_response[7:]
        if clean_response.startswith("```"):
            clean_response = clean_response[3:]
        if clean_response.endswith("```"):
            clean_response = clean_response[:-3]

        clean_response = clean_response.strip()

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="llm_node",
            message="LLM response generated",
        )

        return {
            **state,
            "ai_response": clean_response
        }

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="llm_node",
            message="LLM node failed",
            stack_trace=traceback.format_exc(),
        )

        return {
            **state,
            "ai_response": "Something went wrong while processing your request",
            "status": "failed"
        }


async def end_node(state: GraphState) -> GraphState:
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="end_node",
        message="Graph execution completed",
    )

    return {
        **state,
        "status": state.get("status", "completed")
    }