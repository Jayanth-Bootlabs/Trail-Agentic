from pydantic import BaseModel

class StartRequirementRequest(BaseModel):
    validation_session_id: int