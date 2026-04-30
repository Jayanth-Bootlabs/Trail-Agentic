from pydantic import BaseModel


class StartRequirementRequest(BaseModel):
    validation_session_id: int


class ContinueRequirementRequest(BaseModel):
    requirement_session_id: int
    user_reply: str