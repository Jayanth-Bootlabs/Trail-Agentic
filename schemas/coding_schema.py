from pydantic import BaseModel, Field

class StartCodingRequest(BaseModel):
    requirement_session_id: int = Field(..., gt=0)