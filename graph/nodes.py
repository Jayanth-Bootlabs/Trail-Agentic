import traceback
from graph.state import GraphState
from utils.gemini_llm import llm
from utils.logger import log_event
from utils.helper import clean_ai_response
from prompts.requirements_prompt import get_requirements_prompt
from prompts.code_prompt import get_code_prompt
from prompts.unit_test_prompt import get_unit_tests_prompt
from prompts.insights_prompt import get_insights_prompt
from prompts.documentation_prompt import get_documentation_prompt

SERVICE_NAME = "nodes"

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
        prompt = get_code_prompt(state["user_input"])
        response = await llm.generate(prompt)

        parsed = clean_ai_response(response)

        if not parsed or not isinstance(parsed, dict):
            parsed = {
                "status": "partial",
                "message": "Invalid AI response",
                "code": {}
            }

        status = parsed.get("status", "partial")
        parsed["status"] = status

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="coding_node",
            message="Coding node completed",
            metadata={"status": status},
        )

        return {
            **state,
            "ai_response": parsed,
            "status": status
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

async def unit_tests_node(state: GraphState) -> GraphState:
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="unit_tests_node",
        message="Unit Tests Node started",
        metadata={"user_input": state["user_input"]},
    )

    try:
        prompt = get_unit_tests_prompt(state["user_input"])
        response = await llm.generate(prompt)

        parsed = clean_ai_response(response)

        if not parsed or not isinstance(parsed, dict):
            log_event(
                level="WARNING",
                service=SERVICE_NAME,
                function="unit_tests_node",
                message="Invalid JSON response from LLM",
                metadata={"raw_response": response},
            )

            return {
                **state,
                "ai_response": {
                    "status": "failed",
                    "tests": []
                },
                "status": "failed"
            }

        
        tests = parsed.get("tests", [])

        test_code = "\n\n".join(
            t.get("content", "") for t in tests if isinstance(t, dict)
        )

        frameworks_used = [parsed.get("framework")] if parsed.get("framework") else []

        summary = f"{parsed.get('language', '')} - {parsed.get('framework', '')}"

        final_response = {
            "status": parsed.get("status", "success"),
            "test_code": test_code,
            "test_summary": summary,
            "frameworks_used": frameworks_used
        }

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="unit_tests_node",
            message="Unit Tests Node completed",
            metadata={"status": final_response["status"]},
        )

        return {
            **state,
            "ai_response": final_response,
            "status": final_response["status"]
        }

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="unit_tests_node",
            message="Unit Tests Node failed",
            stack_trace=traceback.format_exc(),
        )
        raise

async def insights_node(state:GraphState) -> GraphState:
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="insights_node",
        message="Insights Node started",
    )

    try:
        input_data = state["user_input"]

        prompt = get_insights_prompt(
            input_data.get("requirements", ""),
            input_data.get("code", ""),
            input_data.get("tests", "")
        )

        response=await llm.generate(prompt)

        parsed=clean_ai_response(response)

        if not parsed:
            log_event(
                level="WARNING",
                service=SERVICE_NAME,
                function="insights_node",
                message="Invalid JSON response from LLM",
                metadata={"raw_response":response},
            )

            parsed={
                "status":"invalid",
                "message": "Invalid AI response"
            }

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="insights_node",
            message="Insights node Completed",
            metadata={"status":parsed["status"]},
        )

        return {
            **state,
            "ai_response":parsed,
            "status":parsed["status"]
        }
    
    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="insights_node",
            message="insights node failed",
            stack_trace=traceback.format_exc(),
        )

        raise

async def documentation_node(state:GraphState) ->GraphState:
    log_event(
        level="INFO",
        service=SERVICE_NAME,
        function="documentation_node",
        message="Documentation Node started",
    )

    try:
        input_data = state["user_input"]

        prompt = get_documentation_prompt(
            input_data.get("requirements", ""),
            input_data.get("code", ""),
            input_data.get("tests", ""),
            input_data.get("insights", "")
        )

        response=await llm.generate(prompt)

        parsed=clean_ai_response(response)

        if not parsed:
            log_event(
                level="WARNING",
                service=SERVICE_NAME,
                function="documentation_node",
                message="Invalid JSON response from LLM",
                metadata={"raw_response":response}
            )

            parsed={
                "status":"invalid",
                "message":"Invalid AI response",

            }

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="documentation_node",
            message="Documentation Node completed",
            metadata={"status":parsed["status"]},
        )

        return {
            **state,
            "ai_response":parsed,
            "status":parsed["status"]
        }
    
    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="Documentation Node",
            message="Documentation Node Failed",
            stack_trace=traceback.format_exc(),
        )

        raise