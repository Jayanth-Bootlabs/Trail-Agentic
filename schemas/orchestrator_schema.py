from pydantic import BaseModel


class StartPipelineRequest(BaseModel):
    user_input: str


class ClarifyPipelineRequest(BaseModel):
    user_reply: str