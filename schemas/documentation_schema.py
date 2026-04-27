from pydantic import BaseModel, Field


class DocumentationRequest(BaseModel):
    insights_test_session_id: int = Field(..., gt=0)

class DocumentationResponse(BaseModel):
    insights_test_session_id: int
    data: dict


