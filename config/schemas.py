# ---------- SCHEMAS ----------

from typing import List

from pydantic import BaseModel, Field

# ----- MAPPING -----

SKILL_ALIAS_MAP = {
    "py": "Python",
    "python3": "Python",
    "python": "Python",
    "js": "JavaScript",
    "node": "Node.js",
    "nodejs": "Node.js",
    "reactjs": "React",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "postgres": "PostgreSQL",
    "sql": "SQL",
}

# ----- PROMPTING -----

OUTPUT_SCHEMA = """
The output must be valid JSON matching this schema exactly:

{
  "name": "",
  "core_languages": [],
  "frameworks_and_libraries": [],
  "tools_and_platforms": [],
  "agentic_ai_experience": [],
  "ai_ml_experience": [],
  "soft_skills": [],
  "projects_mentioned": [],
  "experience_level": {
      "Python": 0,
      "JavaScript": 0,
      "Agentic AI": 0,
      "AI/ML": 0
  },
  "job_search_keywords": []
}

Notes:
- Include fields even if empty.
- "experience_level" MUST contain at least: Python, JavaScript, Agentic AI, AI/ML.
- "projects_mentioned" should be short slugs or titles (no full descriptions).
- job_search_keywords should be realistic search terms.
- Values must be normalized, deduplicated, and concise.
"""

# ----- PYDANTIC -----

class ExperienceLevels(BaseModel):
    """
    asd

    Args:
        BaseModel:
    """

    Python: int = 0
    JavaScript: int = 0
    Agentic_Ai: int = Field(0, alias="Agentic AI")
    AI_ML: int = Field(0, alias="AI/ML")

    class Config:
        """
        asd
        """

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
    """
    A candidate's skill profile.

    Args:
        BaseModel:
    """

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
        """
        asd
        """

        validate_by_name = True
