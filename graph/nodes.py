import traceback
from graph.state import GraphState
from utils.gemini_llm import llm
from utils.logger import log_event
from prompts.validation_prompt import get_validation_prompt

SERVICE_NAME = "graph_nodes"

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

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="llm_node",
            message="LLM response generated",
        )

        return {
            **state,
            "ai_response": response
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
