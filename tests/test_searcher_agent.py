import os
import json
import pytest
from unittest.mock import patch
from agents.searcher import SearcherAgent

# ----------------------------
# Sample skill profile
# ----------------------------
sample_skill_profile = {
    "core_languages": ["Python"],
    "agentic_ai_experience": ["LangChain"],
    "ai_ml_experience": ["TensorFlow"]
}

# ----------------------------
# Mocked scraper results
# ----------------------------
mock_jobs = [
    {
        "title": "Python Developer",
        "company": "Company A",
        "location": "Helsinki",
        "url": "https://duunitori.fi/job/1",
        "published_date": "2025-11-19",
        "description_snippet": "Work with Python",
        "full_description": None,
        "source": "duunitori",
        "query_used": "python developer"
    },
    {
        "title": "Python Developer",
        "company": "Company A",
        "location": "Helsinki",
        "url": "https://duunitori.fi/job/1",  # duplicate
        "published_date": "2025-11-19",
        "description_snippet": "Duplicate",
        "full_description": None,
        "source": "duunitori",
        "query_used": "python developer"
    },
    {
        "title": "Junior AI Engineer",
        "company": "Company B",
        "location": "Espoo",
        "url": "https://duunitori.fi/job/2",
        "published_date": "2025-11-18",
        "description_snippet": "AI work",
        "full_description": None,
        "source": "duunitori",
        "query_used": "ai engineer"
    }
]

# ----------------------------
# Fixture: clean job_listings folder before tests
# ----------------------------
@pytest.fixture(autouse=True)
def clean_job_listings_folder():
    folder = "data/job_listings"
    if os.path.exists(folder):
        for f in os.listdir(folder):
            os.remove(os.path.join(folder, f))
    else:
        os.makedirs(folder)
    yield
    for f in os.listdir(folder):
        os.remove(os.path.join(folder, f))

# ----------------------------
# Test: deduplication
# ----------------------------
#@patch("utils.scraper_duunitori.fetch_search_results", return_value=mock_jobs)
@patch("agents.searcher.fetch_search_results", return_value=mock_jobs)
def test_deduplication(mock_scraper):
    agent = SearcherAgent(job_boards=["duunitori"], deep=False)
    results = agent.search_jobs(sample_skill_profile)
    urls = [job["url"] for job in results]
    assert len(results) == 2
    assert "https://duunitori.fi/job/1" in urls
    assert "https://duunitori.fi/job/2" in urls

# ----------------------------
# Test: raw JSON files are created
# ----------------------------
#@patch("utils.scraper_duunitori.fetch_search_results", return_value=mock_jobs)
@patch("agents.searcher.fetch_search_results", return_value=mock_jobs)
def test_raw_json_saved(mock_scraper):
    agent = SearcherAgent(job_boards=["duunitori"], deep=False)
    _ = agent.search_jobs(sample_skill_profile)
    files = os.listdir("data/job_listings")
    assert len(files) > 0
    for f in files:
        assert f.endswith(".json")
        path = os.path.join("data/job_listings", f)
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
            assert isinstance(data, list)

# ----------------------------
# Test: handles empty skill profile
# ----------------------------
@patch("utils.scraper_duunitori.fetch_search_results", return_value=[])
def test_empty_profile(mock_scraper):
    agent = SearcherAgent(job_boards=["duunitori"], deep=False)
    results = agent.search_jobs({})
    assert results == []

# ----------------------------
# Test: multiple job boards (mocked)
# ----------------------------
#@patch("utils.scraper_duunitori.fetch_search_results", return_value=mock_jobs)
@patch("agents.searcher.fetch_search_results", return_value=mock_jobs)
def test_multiple_job_boards(mock_scraper):
    agent = SearcherAgent(job_boards=["duunitori", "jobly"], deep=False)
    results = agent.search_jobs(sample_skill_profile)
    # jobly returns empty, so total deduplicated jobs = 2
    assert len(results) == 2
