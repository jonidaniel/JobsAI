# ---------- TESTS FOR SCORER AGENT ----------

import pytest

from agents import ScorerAgent
from agents import SkillProfile

# --- MOCK DATA ---

mock_profile_data = {
    "name": "Joni",
    "core_languages": ["Python", "JavaScript"],
    "frameworks_and_libraries": ["React"],
    "tools_and_platforms": ["Docker"],
    "agentic_ai_experience": ["LangChain"],
    "ai_ml_experience": ["TensorFlow"],
    "soft_skills": ["Teamwork"],
    "projects_mentioned": ["Job seeker bot"],
    "experience_level": {"Python": 2, "JavaScript": 2, "Agentic AI": 1, "AI/ML": 1},
    "job_search_keywords": ["llm engineer", "junior software developer"]
}

mock_jobs = [
    {
        "title": "Junior Python Developer",
        "description_snippet": "Looking for a Python dev familiar with Docker and LangChain",
        "full_description": "Experience with TensorFlow is a plus",
        "url": "https://example.com/job1"
    },
    {
        "title": "Senior JavaScript Engineer",
        "description_snippet": "Expert in React and Node.js",
        "full_description": "Some experience with AI/ML is useful",
        "url": "https://example.com/job2"
    },
    {
        "title": "LLM Engineer",
        "description_snippet": "Agentic AI, LangChain, Python",
        "full_description": "",
        "url": "https://example.com/job3"
    }
]

@pytest.fixture
def skill_profile():
    return SkillProfile(**mock_profile_data)

@pytest.fixture
def scorer():
    return ScorerAgent()

# --- TESTS ---

def test_score_jobs_basic(scorer, skill_profile):
    scored = scorer.score_jobs(mock_jobs, skill_profile)
    assert len(scored) == 3
    # Check that score field exists
    for job in scored:
        assert "score" in job
        assert 0 <= job["score"] <= 100
        assert "matched_skills" in job
        assert "missing_skills" in job

def test_sorting_by_score(scorer, skill_profile):
    scored = scorer.score_jobs(mock_jobs, skill_profile)
    scores = [job["score"] for job in scored]
    assert scores == sorted(scores, reverse=True)

def test_agentic_ai_weighting(scorer, skill_profile):
    # The LLM/Agentic AI job should be top
    scored = scorer.score_jobs(mock_jobs, skill_profile)
    top_job = scored[0]
    assert "llm" in top_job["title"].lower() or "agentic" in top_job["title"].lower()

def test_matched_and_missing_skills(scorer, skill_profile):
    scored = scorer.score_jobs(mock_jobs, skill_profile)
    for job in scored:
        # matched + missing should cover all profile keywords
        total_keywords = set(
            skill_profile.core_languages +
            skill_profile.agentic_ai_experience +
            skill_profile.ai_ml_experience +
            skill_profile.job_search_keywords
        )
        combined = set(job["matched_skills"] + job["missing_skills"])
        assert combined == set(map(str, total_keywords))
