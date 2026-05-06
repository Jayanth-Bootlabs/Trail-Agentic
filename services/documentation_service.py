import traceback
import json
import inspect
from fastapi import HTTPException
from models.insights_model import Insights
from models.unit_tests_model import UnitTests
from models.code_model import GeneratedCode
from models.requirements_model import RequirementSession
from models.documentation_model import Documentation
from prompts.documentation_prompt import get_documentation_prompt
from utils.gemini_llm import GeminiLLM
from utils.logger import log_event

SERVICE_NAME = "documentation_service"


async def generate_documentation_service(payload):
    try:
        insights_id = payload.insights_id

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate_documentation_service",
            message="Documentation generation started",
            metadata={"insights_id": insights_id}
        )

        insights_record = await Insights.get_or_none(id=insights_id, is_completed=True)

        if not insights_record:
            raise HTTPException(
                status_code=404,
                detail="Insights not found or insights generation is not completed yet"
            )

        tests_record = await UnitTests.get_or_none(id=insights_record.tests_id)

        if not tests_record:
            raise HTTPException(status_code=404, detail="Unit tests not found")

        code_record = await GeneratedCode.get_or_none(id=tests_record.code_id)

        if not code_record:
            raise HTTPException(status_code=404, detail="Generated code not found")

        requirement_record = await RequirementSession.get_or_none(id=code_record.requirement_id)

        if not requirement_record:
            raise HTTPException(status_code=404, detail="Requirement session not found")

        code_payload = getattr(code_record, "code_json", None)

        if code_payload is None:
            raise HTTPException(status_code=500, detail="Generated code payload is empty")

        code_for_prompt = code_payload if isinstance(code_payload, dict) else str(code_payload)
        tests_content = getattr(tests_record, "test_code", "") or ""

        prompt = get_documentation_prompt(
            requirements_json=requirement_record.combined_input,
            code_content=code_for_prompt,
            test_content=tests_content
        )

        llm = GeminiLLM()
        response = llm.invoke(prompt)

        if inspect.isawaitable(response):
            response = await response

        if not response:
            raise HTTPException(status_code=500, detail="Empty response from LLM")

        cleaned = response.strip().replace("```json", "").replace("```", "")

        try:
            doc_data = json.loads(cleaned)

        except Exception:
            log_event(
                level="ERROR",
                service=SERVICE_NAME,
                function="generate_documentation_service",
                message="Failed to parse AI response for documentation",
                metadata={"raw_response": cleaned}
            )
            raise HTTPException(status_code=500, detail="Invalid documentation format from AI")

        doc_obj = await Documentation.create(
            insights_id=insights_id,
            is_completed=True,
            **doc_data
        )

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate_documentation_service",
            message="Documentation stored successfully",
            metadata={"doc_id": doc_obj.id}
        )

        return {
            "doc_id": doc_obj.id,
            "insights_id": insights_id,
            "overview": doc_obj.overview,
            "architecture": doc_obj.architecture,
            "file_responsibilities": doc_obj.file_responsibilities,
            "functional_requirements": doc_obj.functional_requirements,
            "non_functional_requirements": doc_obj.non_functional_requirements,
            "tech_stack_used": doc_obj.tech_stack_used,
            "assumptions": doc_obj.assumptions,
            "test_summary": doc_obj.test_summary,
            "next_steps": doc_obj.next_steps,
            "created_at": str(doc_obj.created_at) if doc_obj.created_at else None,
        }

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="generate_documentation_service",
            message="Documentation generation failed",
            metadata={"trace": traceback.format_exc()}
        )
        raise HTTPException(status_code=500, detail="Internal server error")


async def get_documentation_service(documentation_id: int):
    try:
        log_event(
            level="INFO", 
            service=SERVICE_NAME, 
            function="get_documentation_service",
            message="Fetching documentation", 
            metadata={"documentation_id": documentation_id})

        doc = await Documentation.get_or_none(id=documentation_id)

        if not doc:
            raise HTTPException(status_code=404, detail="Documentation not found")

        return {
            "doc_id": doc.id,
            "insights_id": doc.insights_id,
            "overview": doc.overview,
            "architecture": doc.architecture,
            "file_responsibilities": doc.file_responsibilities,
            "functional_requirements": doc.functional_requirements,
            "non_functional_requirements": doc.non_functional_requirements,
            "tech_stack_used": doc.tech_stack_used,
            "assumptions": doc.assumptions,
            "test_summary": doc.test_summary,
            "next_steps": doc.next_steps,
            "created_at": str(doc.created_at) if doc.created_at else None,
        }

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR", 
            service=SERVICE_NAME, 
            function="get_documentation_service",
            message="Failed to fetch documentation", 
            metadata={"trace": traceback.format_exc()}
            )
        raise HTTPException(status_code=500, detail="Internal server error")