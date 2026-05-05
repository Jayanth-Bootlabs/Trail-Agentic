from pydantic import BaseModel
from typing import Optional, Dict, List


class CodeGenerationRequest(BaseModel):
    session_id: int
    user_id:int


class CodeGenerationResponse(BaseModel):
    code_id: int
    user_id: int
    session_id: int


    project_title: str
    tech_stack: List[str]
    file_structure: List[str]
    source_code: Dict[str, str]

    created_at: Optional[str]
