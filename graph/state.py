from typing import TypedDict, Optional

class GraphState(TypedDict, total=False):
    user_input: str
    ai_response: Optional[str]
    status: str