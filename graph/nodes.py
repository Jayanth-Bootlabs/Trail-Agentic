import traceback
from graph.state import GraphState
from utils.gemini_llm import llm
from utils.logger import log_event
from prompts.validation_prompt import get_validation_prompt
from prompts.requirements_prompt import get_requirements_prompt
from prompts.insights_prompt import get_insights_prompt
from prompts.documentation_prompt import get_documentation_prompt

SERVICE_NAME = "graph_nodes"

async def validation_node(state: GraphState) -> GraphState:
    try:
        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="validation_node",
            message="prompt validation started",
        )

        prompt = get_validation_prompt(state["user_input"])
        
        response = await llm.generate(prompt)

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="validation_node",
            message="prompt validation completed",
        )

        return {
            **state,
            "ai_response": response,
            "status": "validation_done"
        }

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="validation_node",
            message="prompt validation failed",
            stack_trace=traceback.format_exc(),
        )

        return {
            **state,
            "ai_response": "Something went wrong while checking your input",
            "status": "failed"
        }


async def requirements_node(state: GraphState) -> GraphState:
    try:
        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="requirements_node",
            message="Requirements generation started",
        )

        prompt = get_requirements_prompt(state["user_input"])
        
        response = await llm.generate(prompt)

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="requirements_node",
            message="Requirements generated",
        )

        return {
            **state,
            "ai_response": response,
            "status": "requirements_done"
        }

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="requirements_node",
            message="Requirements generation failed",
            stack_trace=traceback.format_exc(),
        )

        return {
            **state,
            "ai_response": "Something went wrong while getting your requirements",
            "status": "failed"
        }
    


async def insights_node(state:GraphState) -> GraphState:
    try:
        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="insights_node",
            message="Insights generation started",
        )

        prompt=get_insights_prompt(state["user_input"])

        response=await llm.generate(prompt)

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="insights_node",
            message="Insights generation completed",
        )

        return {
            **state,
            "ai_response":response,
            "status":"insights_generation_done"
        }
    
    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="insights_node",
            message="insights generation FAILED",
            stack_trace=traceback.format_exc(),
        )

        return{
            **state,
            "ai_response":"Something went wrong",
            "status":"failed"
        }
    

async def documentation_node(state:GraphState) ->GraphState:
    try:
        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="documentation_node",
            message="Document generation started",
        )

        prompt=get_documentation_prompt(state["user_input"])

        response=await llm.generate(prompt)

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="documentation_node",
            message="Document Generation Completed",
        )

        return {
            **state,
            "ai_response":response,
            "status":"document_generation_done"
        }
    
    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="documentation_node",
            message="Document Generation FAILED",
            stack_trace=traceback.format_exc(),
        )

        return{
            **state,
            "ai_response":"Something wentwrong",
            "status":"Failed"
        }