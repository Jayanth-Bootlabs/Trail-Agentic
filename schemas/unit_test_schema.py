from pydantic import BaseModel


class UnitTestRequest(BaseModel):
    code_id: int