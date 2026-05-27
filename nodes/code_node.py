import traceback
from graph.state import GraphState
from prompts.code_prompt import get_code_prompt
from utils.gemini_llm import llm
from utils.logger import log_event
from utils.helper import clean_ai_response

SERVICE_NAME = "code_node"


async def code_node(state: GraphState) -> GraphState:

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="code_node",
        message="Code node started",
        metadata={
            "has_user_input": "user_input" in state,
        },
    )

    try:
        prompt = get_code_prompt(
            state["user_input"]
        )

        response = await llm.generate(prompt)
        parsed = clean_ai_response(response)

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="code_node",
            message="Parsed AI response structure",
            metadata={"parsed_keys": list(parsed.keys()) if parsed else []},
        )

        if not parsed:

            log_event(
                level="WARNING",
                service=SERVICE_NAME,
                function="code_node",
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
            function="code_node",
            message="Code node completed",
            metadata={"status": normalized_status},
        )

        return {
            **state,
            "code": parsed,
            "status": normalized_status,
        }

    except Exception:

        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="code_node",
            message="Code node failed",
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
        metadata={"retry_count": retry_count},
    )

    return {
        **state,
        "retry_count": retry_count,
    }