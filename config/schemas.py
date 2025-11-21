# ---------- SCHEMAS (PYDANTIC) ----------

from typing import List

from pydantic import BaseModel, Field

class ExperienceLevels(BaseModel):
    Python: int = 0
    JavaScript: int = 0
    Agentic_Ai: int = Field(0, alias="Agentic AI")
    AI_ML: int = Field(0, alias="AI/ML")

    class Config:
        validate_by_name = True
        json_schema_extra = {
            "example": {
                "Python": 7,
                "JavaScript": 6,
                "Agentic AI": 5,
                "AI/ML": 4
            }
        }

class SkillProfile(BaseModel):
    name: str = ""
    core_languages: List[str] = []
    frameworks_and_libraries: List[str] = []
    tools_and_platforms: List[str] = []
    agentic_ai_experience: List[str] = []
    ai_ml_experience: List[str] = []
    soft_skills: List[str] = []
    projects_mentioned: List[str] = []
    experience_level: ExperienceLevels = Field(default_factory=ExperienceLevels)
    job_search_keywords: List[str] = []

    class Config:
        validate_by_name = True
