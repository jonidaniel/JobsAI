"""
Profile Schemas for Internal Data Structures.

This module defines Pydantic models for internal data structures used throughout
the pipeline, specifically for representing candidate skill profiles and experience levels.

Key Models:
    - ExperienceLevels: Maps numeric experience values to descriptive strings
    - SkillProfile: Structure for candidate skill profiles (used by ProfilerAgent)
"""

from typing import List

from pydantic import BaseModel, Field, ConfigDict


class ExperienceLevels(BaseModel):
    """
    Experience level ratings for key technology areas.

    Values represent years of experience on a scale:
    - 0: No experience
    - 1: Less than half a year
    - 2: Less than a year
    - 3: Less than 1.5 years
    - 4: Less than 2 years
    - 5: Less than 2.5 years
    - 6: Less than 3 years
    - 7: Over 3 years

    Fields use aliases to support both Python naming conventions and
    display-friendly names (e.g., "Agentic AI" contains a space).
    """

    Python: int = 0
    JavaScript: int = 0
    Agentic_Ai: int = Field(0, alias="Agentic AI")
    AI_ML: int = Field(0, alias="AI/ML")

    model_config = ConfigDict(
        # Allows access by both field name and alias
        populate_by_name=True,
        # Example values for API documentation
        json_schema_extra={
            "example": {"Python": 7, "JavaScript": 6, "Agentic AI": 5, "AI/ML": 4}
        },
    )


class SkillProfile(BaseModel):
    """
    A candidate's comprehensive skill profile.

    This is the central data structure that represents a candidate's skills,
    experience, and qualifications. It's created by the ProfilerAgent from
    form submissions and used throughout the pipeline for:
    - Generating job search queries
    - Scoring job relevancy
    - Writing personalized cover letters

    All list fields are automatically deduplicated and normalized during processing.
    """

    name: str = ""  # Candidate's name (optional)
    core_languages: List[str] = []  # Programming languages (Python, JavaScript, etc.)
    frameworks_and_libraries: List[str] = (
        []
    )  # Frameworks and libraries (React, FastAPI, etc.)
    tools_and_platforms: List[str] = []  # Tools and platforms (Docker, AWS, etc.)
    agentic_ai_experience: List[str] = []  # Agentic AI tools/technologies
    ai_ml_experience: List[str] = []  # AI/ML technologies and tools
    soft_skills: List[str] = []  # Soft skills (communication, teamwork, etc.)
    projects_mentioned: List[str] = []  # Project names/titles mentioned
    experience_level: ExperienceLevels = Field(
        default_factory=ExperienceLevels
    )  # Experience ratings
    job_search_keywords: List[str] = []  # Additional keywords for job searching

    model_config = ConfigDict(
        # Allows access by both field name and alias
        populate_by_name=True,
    )
