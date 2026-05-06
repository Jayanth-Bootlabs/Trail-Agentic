from pydantic import BaseModel


class GenerateInsightsRequest(BaseModel):
    unit_test_id: int