from pydantic import BaseModel


class CodeGenerationRequest(BaseModel):
    requirements_id: int