import traceback
from graph.state import GraphState
from prompts.insights_prompt import get_insights_prompt
from utils.gemini_llm import llm
from utils.logger import log_event
from utils.helper import clean_ai_response

SERVICE_NAME = "insights_node"


async def insights_node(state: GraphState) -> GraphState:

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="insights_node",
        message="Insights node started",
        metadata={
            "has_requirements": "requirements" in state,
            "has_code": "code" in state,
            "has_test_code": "test_code" in state,
        },
    )

    try:
        prompt = get_insights_prompt(
            state["requirements"],
            state["code"],
            state["test_code"],
        )

        response = await llm.generate(prompt)
        parsed = clean_ai_response(response)

        if not parsed:

            log_event(
                level="WARNING",
                service=SERVICE_NAME,
                function="insights_node",
                message="Invalid JSON response from LLM",
                metadata={
                    "raw_response": str(response)
                },
            )

            return {
                **state,
                "status": "retry",
            }

        raw_status = parsed.get("status", "invalid")
        normalized_status = "valid" if raw_status in ("success", "completed") else raw_status
        parsed["status"] = normalized_status

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="insights_node",
            message="Insights node completed",
            metadata={
                "status": normalized_status
            },
        )

        return {
            **state,
            "insights": parsed,
            "status": normalized_status,
        }

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="insights_node",
            message="Insights node failed",
            stack_trace=traceback.format_exc(),
        )
        raise


async def retry_node(state: GraphState) -> GraphState:

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="retry_node",
        message="Retry node started",
    )

    retry_count = state.get("retry_count", 0) + 1

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="retry_node",
        message="Retry count updated",
        metadata={
            "retry_count": retry_count
        }
    )

    return {
        **state,
        "retry_count": retry_count,
    }