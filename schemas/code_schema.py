from pydantic import BaseModel

class CodeRequest(BaseModel):
    requirement_id: int