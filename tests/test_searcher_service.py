# ---------- TESTS FOR SEARCHER SERVICE ----------

import os
import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from jobsai.agents.searcher import SearcherService
from jobsai.utils.exceptions import CancellationError

# ----------------------------
# Mock data
# ----------------------------

mock_keywords = ["python developer", "ai engineer"]

mock_jobs_duunitori = [
    {
        "title": "Python Developer",
        "company": "Company A",
        "location": "Helsinki",
        "url": "https://duunitori.fi/job/1",
        "description_snippet": "Work with Python",
        "full_description": None,
        "source": "duunitori",
    },
    {
        "title": "Python Developer",
        "company": "Company A",
        "location": "Helsinki",
        "url": "https://duunitori.fi/job/1",  # duplicate
        "description_snippet": "Duplicate",
        "full_description": None,
        "source": "duunitori",
    },
    {
        "title": "Junior AI Engineer",
        "company": "Company B",
        "location": "Espoo",
        "url": "https://duunitori.fi/job/2",
        "description_snippet": "AI work",
        "full_description": None,
        "source": "duunitori",
    },
]

mock_jobs_jobly = [
    {
        "title": "Python Developer",
        "company": "Company C",
        "location": "Tampere",
        "url": "https://jobly.fi/job/1",
        "description_snippet": "Python position",
        "full_description": None,
        "source": "jobly",
    },
]


# ----------------------------
# Fixture: clean job_listings folder before tests
# ----------------------------
@pytest.fixture(autouse=True)
def clean_job_listings_folder():
    """Clean up job listings folder before and after tests."""
    from jobsai.config.paths import RAW_JOB_LISTING_PATH

    folder = RAW_JOB_LISTING_PATH
    if os.path.exists(folder):
        for f in os.listdir(folder):
            file_path = os.path.join(folder, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
    else:
        os.makedirs(folder, exist_ok=True)
    yield
    # Cleanup after test
    if os.path.exists(folder):
        for f in os.listdir(folder):
            file_path = os.path.join(folder, f)
            if os.path.isfile(file_path):
                os.remove(file_path)


# ----------------------------
# Test fixtures
# ----------------------------
@pytest.fixture
def searcher():
    """Create a SearcherService instance for testing."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return SearcherService(timestamp)


# ----------------------------
# Tests
# ----------------------------
@patch("jobsai.agents.searcher.scrape_duunitori", return_value=mock_jobs_duunitori)
def test_deduplication(mock_scraper, searcher):
    """Test that duplicate jobs (same URL) are removed."""
    results = searcher.search_jobs(
        keywords=mock_keywords,
        job_boards=["Duunitori"],
        deep_mode=False,
    )
    urls = [job["url"] for job in results]
    # Should have 2 unique jobs (duplicate removed)
    assert len(results) == 2
    assert "https://duunitori.fi/job/1" in urls
    assert "https://duunitori.fi/job/2" in urls
    # Check no duplicates
    assert len(urls) == len(set(urls))


@patch("jobsai.agents.searcher.scrape_duunitori", return_value=mock_jobs_duunitori)
def test_raw_json_saved(mock_scraper, searcher):
    """Test that raw job listings are saved to JSON files."""
    from jobsai.config.paths import RAW_JOB_LISTING_PATH

    _ = searcher.search_jobs(
        keywords=mock_keywords,
        job_boards=["Duunitori"],
        deep_mode=False,
    )
    files = os.listdir(RAW_JOB_LISTING_PATH)
    assert len(files) > 0
    for f in files:
        assert f.endswith(".json")
        path = os.path.join(RAW_JOB_LISTING_PATH, f)
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
            assert isinstance(data, list)


@patch("jobsai.agents.searcher.scrape_duunitori", return_value=[])
def test_empty_results(mock_scraper, searcher):
    """Test that empty scraper results return empty list."""
    results = searcher.search_jobs(
        keywords=mock_keywords,
        job_boards=["Duunitori"],
        deep_mode=False,
    )
    assert results == []


@patch("jobsai.agents.searcher.scrape_jobly", return_value=mock_jobs_jobly)
@patch("jobsai.agents.searcher.scrape_duunitori", return_value=mock_jobs_duunitori)
def test_multiple_job_boards(mock_duunitori, mock_jobly, searcher):
    """Test searching multiple job boards."""
    results = searcher.search_jobs(
        keywords=mock_keywords,
        job_boards=["Duunitori", "Jobly"],
        deep_mode=False,
    )
    # Should have jobs from both boards (deduplicated)
    assert len(results) >= 2
    # Check that both scrapers were called
    assert mock_duunitori.called
    assert mock_jobly.called


@patch("jobsai.agents.searcher.scrape_duunitori", return_value=mock_jobs_duunitori)
def test_deep_mode_passed_to_scraper(mock_scraper, searcher):
    """Test that deep_mode parameter is passed to scrapers."""
    searcher.search_jobs(
        keywords=mock_keywords,
        job_boards=["Duunitori"],
        deep_mode=True,
    )
    # Check that scrape_duunitori was called with deep_mode=True
    assert mock_scraper.called
    call_args = mock_scraper.call_args
    assert call_args.kwargs.get("deep_mode") is True


@patch("jobsai.agents.searcher.scrape_duunitori", return_value=mock_jobs_duunitori)
def test_cancellation_check(mock_scraper, searcher):
    """Test that cancellation check works during search."""
    cancellation_called = False

    def cancellation_check():
        nonlocal cancellation_called
        cancellation_called = True
        return True

    with pytest.raises(CancellationError):
        searcher.search_jobs(
            keywords=mock_keywords,
            job_boards=["Duunitori"],
            deep_mode=False,
            cancellation_check=cancellation_check,
        )
    assert cancellation_called


@patch("jobsai.agents.searcher.scrape_duunitori", return_value=mock_jobs_duunitori)
def test_unknown_job_board_skipped(mock_scraper, searcher):
    """Test that unknown job boards are skipped gracefully."""
    results = searcher.search_jobs(
        keywords=mock_keywords,
        job_boards=["Duunitori", "UnknownBoard"],
        deep_mode=False,
    )
    # Should still return results from known board
    assert len(results) > 0
