from pydantic import BaseModel

class ValidateRequest(BaseModel):
    user_input: str

class ContinueRequest(BaseModel):
    session_id: int
    user_reply: str