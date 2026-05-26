from typing import TypedDict, Optional, List, Dict, Any


class GraphState(TypedDict, total=False):
    status: str
    error: Optional[str]
    retry_count: int
    history: List[Dict[str, Any]]
    messages: List[str]
    reasoning: List[str]
    attempts: int

    user_name: str 
    user_input: Any

    ai_response: Dict[str, Any]

    requirements: Any
    code: Any
    test_code: Any
    unit_tests: Dict[str, Any]
    insights: Dict[str, Any]
    documentation: Dict[str, Any]