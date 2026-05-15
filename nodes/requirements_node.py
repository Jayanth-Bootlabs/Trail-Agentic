import traceback
from graph.state import GraphState
from prompts.requirements_prompt import get_requirements_prompt
from utils.gemini_llm import llm
from utils.logger import log_event
from utils.helper import clean_ai_response

SERVICE_NAME = "requirements_node"


async def requirements_node(state: GraphState) -> GraphState:

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="requirements_node",
        message="Requirements node started",
        metadata={
            "has_user_input": "user_input" in state,
            "has_user_name": "user_name" in state,
        },
    )

    try:
        prompt = get_requirements_prompt(
            user_input=state["user_input"],
            user_name=state.get("user_name", "General User"),
        )

        response = await llm.generate(prompt)
        parsed = clean_ai_response(response)

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="requirements_node",
            message="Parsed AI response structure",
            metadata={"parsed_keys": list(parsed.keys()) if parsed else []},
        )

        history = state.get("history", [])
        reasoning = state.get("reasoning", [])
        messages = state.get("messages", [])

        history.append({
            "node": "requirements_node",
            "response": str(response)
        })

        reasoning.append("Requirements node executed")
        messages.append("Requirements generation completed")

        if not parsed:

            log_event(
                level="WARNING",
                service=SERVICE_NAME,
                function="requirements_node",
                message="Invalid JSON response from LLM",
                metadata={
                    "raw_response": str(response)
                },
            )

            return {
                **state,
                "status": "retry",
                "history": history,
                "reasoning": reasoning,
                "messages": messages,
            }

        raw_status = parsed.get("status", "invalid")
        normalized_status = "valid" if raw_status in ("success", "completed") else raw_status
        parsed["status"] = normalized_status

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="requirements_node",
            message="Requirements node completed",
            metadata={"status": normalized_status},
        )

        return {
            **state,
            "requirements": parsed,    
            "ai_response": parsed,
            "status": normalized_status,
            "history": history,
            "reasoning": reasoning,
            "messages": messages,
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


async def retry_node(state: GraphState) -> GraphState:

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="retry_node",
        message="Retry node started",
    )

    history = state.get("history", [])
    reasoning = state.get("reasoning", [])
    messages = state.get("messages", [])

    retry_count = state.get("retry_count", 0) + 1

    history.append({
        "node": "retry_node",
        "attempt": retry_count
    })

    reasoning.append("Retrying requirements generation")
    messages.append(f"Retry attempt {retry_count}")

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
        "history": history,
        "reasoning": reasoning,
        "messages": messages,
    }