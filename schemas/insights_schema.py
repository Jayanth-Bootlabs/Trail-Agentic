from pydantic import BaseModel, Field


class InsightsRequest(BaseModel):
    unit_test_session_id: int = Field(..., gt=0)

class InsightsResponse(BaseModel):
    unit_test_session_id: int
    data: dict


