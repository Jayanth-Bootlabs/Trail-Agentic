from pydantic import BaseModel

class PromptRequest(BaseModel):
    user_input: str

class PromptResponse(BaseModel):
    session_id: int
    response: str