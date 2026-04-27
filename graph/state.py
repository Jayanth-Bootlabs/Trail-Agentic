from typing import TypedDict

class GraphState(TypedDict, total=False):
    user_input: str
    ai_response: dict
    status: str