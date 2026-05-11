from typing import TypedDict, Optional, List, Dict, Any


class GraphState(TypedDict, total=False):
    user_input: Any
    ai_response: Dict[str, Any]
    status: str

    history: List[Dict[str, Any]]
    attempts: int
    messages: List[str]
    reasoning: List[str]
    error: Optional[str]
    retry_count: int