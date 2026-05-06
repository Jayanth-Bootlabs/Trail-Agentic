import traceback
from fastapi import HTTPException
from models.requirements_model import RequirementSession
from models.coding_model import CodingSession
from graph.builder import build_coding_graph
from utils.logger import log_event

SERVICE_NAME = "coding_service"


async def start_coding_request(payload):
    try:
        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="start_coding_request",
            message="Coding started",
            metadata={"requirement_session_id": payload.requirement_session_id},
        )

        requirement = await RequirementSession.get_or_none(
            id=payload.requirement_session_id
        )

        if not requirement:
            raise HTTPException(status_code=404, detail="Requirement not found")

        if not requirement.is_completed:
            raise HTTPException(
                status_code=400,
                detail="Requirements not completed"
            )

        req_data = requirement.ai_response

        if not req_data:
            raise HTTPException(
                status_code=400,
                detail="Missing requirement AI response"
            )

        structured_input = req_data.get("data", {})

        graph = build_coding_graph()

        result = await graph.ainvoke({
            "user_input": structured_input
        })

        ai = result["ai_response"]

        session = await CodingSession.create(
            requirement_session=requirement,
            requirements_input=structured_input,
            status=ai["status"],
            ai_response=ai,
            is_completed=(ai["status"] == "completed")
        )

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="start_coding_request",
            message="Coding completed",
            metadata={"coding_session_id": session.id},
        )

        return {
            "coding_session_id": session.id,
            "status": ai["status"],
            "code": ai.get("code", {})
        }

    except HTTPException:
        raise

    except Exception:
        log_event(
            level="ERROR",
            service=SERVICE_NAME,
            function="start_coding_request",
            message="Coding failed",
            stack_trace=traceback.format_exc(),
        )
        raise HTTPException(status_code=500, detail="Internal server error")