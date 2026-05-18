import traceback
from graph.state import GraphState
from prompts.validation_prompt import get_validation_prompt
from utils.gemini_llm import llm
from utils.logger import log_event
from utils.helper import clean_ai_response


SERVICE_NAME = "validation_node"


async def validate_node(state: GraphState) -> GraphState:

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="validate_node",
        message="Validation node started",
        metadata={
            "user_input": state["user_input"]
        },
    )

    try:

        prompt = get_validation_prompt(
            state["user_input"]
        )

        response = await llm.generate(prompt)
        parsed = clean_ai_response(response)

        history = state.get("history", [])
        reasoning = state.get("reasoning", [])
        messages = state.get("messages", [])

        history.append({
            "node": "validate_node",
            "response": str(response)
        })

        reasoning.append("Validation node executed")
        messages.append("Validation completed")

        if not parsed:

            log_event(
                level="WARNING",
                service=SERVICE_NAME,
                function="validate_node",
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

        parsed["status"] = parsed.get(
            "status",
            "invalid"
        )

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="validate_node",
            message="Validation node completed",
            metadata={
                "status": parsed["status"]
            },
        )

        return {
            **state,
            "ai_response": parsed,
            "status": parsed["status"],
            "history": history,
            "reasoning": reasoning,
            "messages": messages,
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

    reasoning.append(
        "Retrying validation"
    )

    messages.append(
        f"Retry attempt {retry_count}"
    )

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
        "history": history,
        "reasoning": reasoning,
        "messages": messages,
    }


async def clarification_node(state: GraphState) -> GraphState:

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="clarification_node",
        message="Clarification node started",
    )

    history = state.get("history", [])
    messages = state.get("messages", [])

    history.append({
        "node": "clarification_node"
    })

    ai_response = state.get("ai_response", {})

    clarification_message = ai_response.get(
        "message",
        "More information is required"
    )

    messages.append(
        clarification_message
    )

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="clarification_node",
        message="Clarification requested",
    )

    return {
        **state,
        "history": history,
        "messages": messages,
    }


async def rejection_node(state: GraphState) -> GraphState:

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="rejection_node",
        message="Rejection node started",
    )

    history = state.get("history", [])
    messages = state.get("messages", [])

    history.append({
        "node": "rejection_node"
    })

    ai_response = state.get("ai_response", {})

    rejection_message = ai_response.get(
        "message",
        "Request rejected"
    )

    messages.append(
        rejection_message
    )

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="rejection_node",
        message="Request rejected",
    )

    return {
        **state,
        "history": history,
        "messages": messages,
    }