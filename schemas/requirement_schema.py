from pydantic import BaseModel

class RequirementRequest(BaseModel):
    session_id: int