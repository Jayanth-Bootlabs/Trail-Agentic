from pydantic import BaseModel


class GenerateDocumentationRequest(BaseModel):
    insights_id: int