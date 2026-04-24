from pydantic import BaseModel, Field

class RequirementsRequest(BaseModel):
    prompt_session_id: int = Field(..., gt=0)

class RequirementsResponse(BaseModel):
    requirement_session_id: int
    data: dict