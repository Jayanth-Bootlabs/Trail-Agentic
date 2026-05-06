from pydantic import BaseModel
from typing import List, Optional


class UnitTestRequest(BaseModel):
    code_id: int


class UnitTestFetchRequest(BaseModel):
    unit_test_id: int


class UnitTestResponse(BaseModel):
    test_id: int
    code_id: int

    test_code: str
    test_summary: Optional[str]
    frameworks_used: List[str]

    created_at: Optional[str]