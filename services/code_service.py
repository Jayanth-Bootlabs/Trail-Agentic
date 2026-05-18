import traceback
from fastapi import HTTPException
from builder.code_builder import build_code_graph
from schemas.code_schema import CodeGenerationRequest
from models.requirements_model import RequirementSession
from models.code_model import GeneratedCode
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

        graph = build_code_graph()

        config = {
            "configurable": {
                "thread_id": f"code-{requirements_id}"
            }
        }

        result = await graph.ainvoke(
            {
                "user_input": requirement.user_input,
                "history": [],
                "attempts": 0,
                "messages": [],
                "reasoning": [],
                "retry_count": 0
            },
            config=config
        )

        ai = result.get("code", {})

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate_code_service",
            message="Code data from state",
            metadata={"ai_keys": list(ai.keys()) if ai else []},
        )

        source_code = ai.get("source_code", {})
        is_completed = (
            result.get("status") == "valid"
            and isinstance(source_code, dict)
            and len(source_code) > 0
        )

        code_obj = await GeneratedCode.create(
            requirement=requirement,
            code_json=ai,
            is_completed=is_completed,
        )

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate_code_service",
            message="Code stored successfully",
            metadata={
                "code_id": code_obj.id,
                "requirements_id": requirements_id,
                "status": result.get("status"),
            },
        )

        return {
            "code_id": code_obj.id,
            "requirements_id": requirements_id,
            "project_title": ai.get("project_title", ""),
            "tech_stack": ai.get("tech_stack", []),
            "file_structure": ai.get("file_structure", []),
            "source_code": source_code,
            "is_completed": is_completed,
            "created_at": str(code_obj.created_at) if code_obj.created_at else None,
            "status": result.get("status"),
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
            metadata={"code_id": code_id},
        )

        code_record = await GeneratedCode.get_or_none(id=code_id)

        if not code_record:
            raise HTTPException(status_code=404, detail="Generated code not found")

        code_data = code_record.code_json or {}

        return {
            "code_id": code_record.id,
            "requirements_id": code_record.requirement_id,
            "project_title": code_data.get("project_title", ""),
            "tech_stack": code_data.get("tech_stack", []),
            "file_structure": code_data.get("file_structure", []),
            "source_code": code_data.get("source_code", {}),
            "is_completed": code_record.is_completed,
            "created_at": str(code_record.created_at) if code_record.created_at else None,
        }

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="get_generated_code_service",
            message="Fetching code failed",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")