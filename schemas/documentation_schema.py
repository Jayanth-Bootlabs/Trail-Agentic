from pydantic import BaseModel
from typing import List, Optional


class GenerateDocumentationRequest(BaseModel):
    insights_id: int


class FetchDocumentationRequest(BaseModel):
    documentation_id: int


class DocumentationResponse(BaseModel):
    doc_id: int
    insights_id: int

    overview: str
    architecture: str

    file_responsibilities: List[str]
    functional_requirements: List[str]
    non_functional_requirements: List[str]
    tech_stack_used: List[str]
    assumptions: List[str]

    test_summary: str
    next_steps: List[str]

    created_at: Optional[str]