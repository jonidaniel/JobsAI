# ---------- TESTS FOR SCORER SERVICE ----------

import pytest
from datetime import datetime

from jobsai.agents.scorer import ScorerService

# --- MOCK DATA ---

# Tech stack format: List[List[Dict[str, Union[int, str]]]]
# Each inner list represents a technology category
mock_tech_stack = [
    [{"Python": 5}, {"JavaScript": 3}],  # languages
    [{"React": 4}],  # web-frameworks
    [{"Docker": 3}],  # cloud-development
    [{"LangChain": 2}],  # llms
    [{"TensorFlow": 1}],  # llms
]

mock_jobs = [
    {
        "title": "Junior Python Developer",
        "description_snippet": "Looking for a Python dev familiar with Docker and LangChain",
        "full_description": "Experience with TensorFlow is a plus",
        "url": "https://example.com/job1",
        "company": "Company A",
        "location": "Helsinki",
    },
    {
        "title": "Senior JavaScript Engineer",
        "description_snippet": "Expert in React and Node.js",
        "full_description": "Some experience with AI/ML is useful",
        "url": "https://example.com/job2",
        "company": "Company B",
        "location": "Espoo",
    },
    {
        "title": "LLM Engineer",
        "description_snippet": "Agentic AI, LangChain, Python",
        "full_description": "",
        "url": "https://example.com/job3",
        "company": "Company C",
        "location": "Tampere",
    },
]


@pytest.fixture
def scorer():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return ScorerService(timestamp)


# --- TESTS ---


def test_score_jobs_basic(scorer):
    """Test that scoring adds score, matched_skills, and missing_skills fields."""
    scored = scorer.score_jobs(mock_jobs, mock_tech_stack)
    assert len(scored) == 3
    # Check that score field exists
    for job in scored:
        assert "score" in job
        assert 0 <= job["score"] <= 100
        assert "matched_skills" in job
        assert "missing_skills" in job
        assert isinstance(job["matched_skills"], list)
        assert isinstance(job["missing_skills"], list)


def test_sorting_by_score(scorer):
    """Test that jobs are sorted by score in descending order."""
    scored = scorer.score_jobs(mock_jobs, mock_tech_stack)
    scores = [job["score"] for job in scored]
    assert scores == sorted(scores, reverse=True)


def test_llm_job_high_score(scorer):
    """Test that LLM-related jobs get higher scores when tech stack includes LLM skills."""
    scored = scorer.score_jobs(mock_jobs, mock_tech_stack)
    # The LLM Engineer job should score well because it matches LangChain and Python
    llm_job = next((job for job in scored if "LLM" in job["title"]), None)
    assert llm_job is not None
    assert llm_job["score"] > 0
    # Should have matched skills
    assert len(llm_job["matched_skills"]) > 0


def test_matched_and_missing_skills(scorer):
    """Test that matched and missing skills are correctly identified."""
    scored = scorer.score_jobs(mock_jobs, mock_tech_stack)
    for job in scored:
        # matched_skills should contain technologies found in job description
        assert isinstance(job["matched_skills"], list)
        # missing_skills should contain technologies not found
        assert isinstance(job["missing_skills"], list)
        # All tech stack items should be in either matched or missing
        # (flatten tech_stack for comparison)
        all_techs = []
        for category in mock_tech_stack:
            for item in category:
                all_techs.extend(item.keys())
        # Normalize for comparison (case-insensitive)
        matched_lower = [s.lower() for s in job["matched_skills"]]
        missing_lower = [s.lower() for s in job["missing_skills"]]
        all_techs_lower = [t.lower() for t in all_techs]
        combined = set(matched_lower + missing_lower)
        assert combined.issubset(set(all_techs_lower))


def test_empty_jobs_list(scorer):
    """Test that empty job list returns empty list."""
    scored = scorer.score_jobs([], mock_tech_stack)
    assert scored == []


def test_empty_tech_stack(scorer):
    """Test that empty tech stack results in 0% scores."""
    scored = scorer.score_jobs(mock_jobs, [])
    for job in scored:
        assert job["score"] == 0
        assert len(job["matched_skills"]) == 0


def test_cancellation_check(scorer):
    """Test that cancellation check works during scoring."""
    cancellation_called = False

    def cancellation_check():
        nonlocal cancellation_called
        cancellation_called = True
        return True

    from jobsai.utils.exceptions import CancellationError

    with pytest.raises(CancellationError):
        scorer.score_jobs(mock_jobs, mock_tech_stack, cancellation_check)
    assert cancellation_called
