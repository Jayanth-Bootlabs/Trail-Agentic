import traceback

from graph.state import GraphState
from prompts.validation_prompt import get_validation_prompt
from utils.model_router import llm
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

        response = await llm.generate_for_node(
            prompt, "validation_node", request_context=state["user_input"]
        )

        parsed = clean_ai_response(response)

        messages = state.get("messages", [])

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

            fallback_response = {
                "status": "retry",
                "message": "Invalid AI response"
            }

            return {
                **state,
                "ai_response": fallback_response,
                "status": "retry",
                "messages": messages,
            }

        parsed["status"] = parsed.get(
            "status",
            "invalid"
        )

        parsed["message"] = parsed.get(
            "message",
            "No response generated"
        )

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="validate_node",
            message="Validation node completed",
            metadata={
                "status": parsed["status"],
                "message": parsed["message"]
            },
        )

        return {
            **state,
            "ai_response": parsed,
            "status": parsed["status"],
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

    messages = state.get("messages", [])


    retry_count = state.get("retry_count", 0) + 1

    messages.append(f"Retry attempt {retry_count}")

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
        "messages": messages,
    }


async def clarification_node(state: GraphState) -> GraphState:

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="clarification_node",
        message="Clarification node started",
    )

    messages = state.get("messages", [])

    ai_response = state.get("ai_response") or {}

    clarification_message = ai_response.get(
        "message",
        "More information is required"
    )

    messages.append(clarification_message)


    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="clarification_node",
        message="Clarification requested",
        metadata={
            "message": clarification_message
        }
    )

    return {
        **state,
        "messages": messages,
    }


async def rejection_node(state: GraphState) -> GraphState:

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="rejection_node",
        message="Rejection node started",
    )
    
    
    messages = state.get("messages", [])

    ai_response = state.get("ai_response") or {}

    rejection_message = ai_response.get(
        "message",
        "Request rejected"
    )

    messages.append(rejection_message)

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="rejection_node",
        message="Request rejected",
        metadata={
            "message": rejection_message
        }
    )

    return {
        **state,
        "messages": messages,
    }
