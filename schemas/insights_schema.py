from pydantic import BaseModel
from typing import List, Optional


class GenerateInsightsRequest(BaseModel):
    user_id: int
    session_id: int


class InsightsResponse(BaseModel):
    insight_id: int
    user_id: int
    session_id: int
    
    insights_summary: str
    key_insights: List[str]
    missing_implementations: List[str]
    code_quality_issues: List[str]
    security_issues: List[str]
    scalability_problems: List[str]
    refactoring_suggestions: List[str]
    dependencies: List[str]
    recommendations: List[str]

    created_at: Optional[str]






    