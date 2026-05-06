import traceback
from fastapi import HTTPException
from models.requirements_model import RequirementSession
from schemas.code_schema import CodeGenerationRequest
from models.code_model import GeneratedCode
from graph.builder import build_coding_graph
from utils.logger import log_event

SERVICE_NAME = "code_generation_service"

async def generate_code_service(payload: CodeGenerationRequest):
    try:
        requirements_id = payload.requirements_id

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate_code_service",
            message="Code generation started",
            metadata={"requirements_id": requirements_id},
        )

        requirement = await RequirementSession.get_or_none(
            id=requirements_id,
            is_completed=True
        )

        if not requirement:
            raise HTTPException(
                status_code=404,
                detail="Requirement not found or not completed yet"
            )

        structured_input = requirement.user_input

        graph = build_coding_graph()

        result = await graph.ainvoke({
            "user_input": structured_input
        })
        
        code_data = result.get("ai_response")

        if not code_data or not isinstance(code_data, dict):
            code_data = {
                "status": "partial",
                "message": "Invalid AI response",
                "source_code": {}
            }

        source_code = code_data.get("source_code", {})

        if source_code and isinstance(source_code, dict) and len(source_code) > 0:
            code_data["status"] = "completed"
        else:
            code_data["status"] = "partial"

        code_obj = await GeneratedCode.create(
            requirement_id=requirements_id,
            code_json=code_data,
            is_completed=(code_data.get("status") == "completed")
        )

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate_code_service",
            message="Code stored successfully",
            metadata={"code_id": code_obj.id},
        )

        return {
            "code_id": code_obj.id,
            "source_code": code_data.get("source_code", {}),
        }

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="generate_code_service",
            message="Code generation failed",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")
    
async def get_generated_code_service(code_id: int):
    try:
        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="get_generated_code_service",
            message="Fetching generated code",
            metadata={"code_id": code_id}
        )

        code_record = await GeneratedCode.get_or_none(id=code_id)

        if not code_record:
            raise HTTPException(status_code=404, detail="Generated code not found")

        code_data = code_record.code_json or {}

        return {
            "code_id": code_record.id,
            "project_title": code_data.get("project_title", ""),
            "tech_stack": code_data.get("tech_stack", []),
            "file_structure": code_data.get("file_structure", []),
            "source_code": code_data.get("source_code", {}),
        }

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="get_generated_code_service",
            message="Fetching code failed",
            stack_trace=traceback.format_exc()
        )
        raise HTTPException(status_code=500, detail="Internal server error")