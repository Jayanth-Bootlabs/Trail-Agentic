from pydantic import BaseModel

class PromptRequest(BaseModel):
    input: str