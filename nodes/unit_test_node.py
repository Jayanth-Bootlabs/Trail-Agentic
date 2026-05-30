import traceback
from graph.state import GraphState
from prompts.unit_test_prompt import get_unit_tests_prompt
from utils.gemini_llm import llm
from utils.logger import log_event
from utils.helper import clean_ai_response


SERVICE_NAME = "unit_test_node"


async def unit_test_node(state: GraphState) -> GraphState:

    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="unit_test_node",
        message="Unit test node started",
        metadata={
            "code": state["code"]
        },
    )

    try:

        prompt = get_unit_tests_prompt(
            state["code"]
        )

        response = await llm.generate(prompt)

        parsed = clean_ai_response(response)

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="unit_test_node",
            message="Parsed AI response structure",
            metadata={
                "parsed": parsed
            },
        )

        if not parsed:

            log_event(
                level="WARNING",
                service=SERVICE_NAME,
                function="unit_test_node",
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

        
        test_content = "\n\n".join(
            f"# {t.get('file_name', '')}\n{t.get('content', '')}"
            for t in parsed.get("tests", [])
        )

        unit_tests_data = {
            "test_code": test_content,
            "test_summary": f"Language: {parsed.get('language', '')} | Framework: {parsed.get('framework', '')}",
            "frameworks_used": [parsed.get("framework")] if parsed.get("framework") else [],
            "status": normalized_status,
        }

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="unit_test_node",
            message="Unit test node completed",
            metadata={
                "status": normalized_status
            },
        )

        return {
            **state,
            "unit_tests": unit_tests_data,
            "ai_response": parsed,
            "status": normalized_status,
        }

    except Exception:

        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="unit_test_node",
            message="Unit test node failed",
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