from typing import Optional
from pydantic import BaseModel


class ResumeResult(BaseModel):
    filename: str
    candidate_name: Optional[str] = None
    overall_score: int
    skill_score: int
    experience_score: int
    education_score: int
    soft_skill_score: int
    strengths: list[str]
    weaknesses: list[str]
    summary: str
    resume_text: Optional[str] = None
    error: Optional[str] = None


class MatchResponse(BaseModel):
    results: list[ResumeResult]
    total: int
