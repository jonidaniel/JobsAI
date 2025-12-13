# ---------- DUUNITORI SCRAPER TEST ----------

import pytest
from unittest.mock import patch, MagicMock, Mock
import requests
from bs4 import BeautifulSoup

from jobsai.utils.scrapers.duunitori import (
    scrape_duunitori,
    _fetch_page,
    _fetch_full_job_description,
)

# Import private function for testing (not ideal but needed for unit tests)
from jobsai.utils.scrapers.duunitori import _parse_job_card
from jobsai.utils.exceptions import CancellationError


# ------------------------------------------------------------
# Helpers for mock responses
# ------------------------------------------------------------


class MockResponse:
    def __init__(self, text="", status_code=200, content=b""):
        self.text = text
        self.status_code = status_code
        self.content = content


def load_fixture(path):
    """Load HTML fixture as text."""
    import os

    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", path)
    with open(fixture_path, "r", encoding="utf-8") as f:
        return f.read()


# ------------------------------------------------------------
# _parse_job_card Tests
# ------------------------------------------------------------


def test_parse_job_card_basic():
    """Test parsing a basic job card."""
    html = """
    <div class="job-box">
        <h3 class="job-box__title">
            <a href="/tyopaikat/123" class="job-box__hover gtm-search-result">Junior AI Engineer</a>
        </h3>
        <div class="job-box__hover gtm-search-result" data-company="ACME Corp" href="/tyopaikat/123"></div>
        <div class="job-box__job-location">Helsinki</div>
        <div class="job-box__job-posted">2025-02-10</div>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    card = soup.select_one(".job-box")

    job = _parse_job_card(card)

    assert job["title"] == "Junior AI Engineer"
    assert job["company"] == "ACME Corp"
    assert job["location"] == "Helsinki"
    assert "/tyopaikat/123" in job["url"] or "duunitori.fi" in job["url"]
    assert job["source"] == "duunitori"


def test_parse_job_card_missing_fields():
    """Test parsing job card with missing optional fields."""
    html = """
    <div class="job-box">
        <h3 class="job-box__title">
            <a href="/tyopaikat/456" class="job-box__hover gtm-search-result">Developer</a>
        </h3>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    card = soup.select_one(".job-box")

    job = _parse_job_card(card)

    assert job["title"] == "Developer"
    assert job["company"] == ""  # Missing company (no data-company attribute)
    assert job["location"] == ""  # Missing location
    assert "url" in job
    assert job["source"] == "duunitori"


# ------------------------------------------------------------
# _fetch_page Tests
# ------------------------------------------------------------


def test_fetch_page_success():
    """Test successful page fetch."""
    mock_session = MagicMock()
    mock_response = MockResponse(text="<html>Success</html>", status_code=200)
    mock_session.get.return_value = mock_response

    response = _fetch_page(mock_session, "https://example.com", retries=1)

    assert response is not None
    assert response.status_code == 200
    mock_session.get.assert_called_once()


def test_fetch_page_retry_on_failure():
    """Test that page fetch retries on failure."""
    mock_session = MagicMock()
    # First call fails, second succeeds
    mock_session.get.side_effect = [
        requests.RequestException("Connection error"),
        MockResponse(text="<html>Success</html>", status_code=200),
    ]

    response = _fetch_page(mock_session, "https://example.com", retries=2, backoff=0.01)

    assert response is not None
    assert response.status_code == 200
    assert mock_session.get.call_count == 2


def test_fetch_page_handles_429():
    """Test that 429 (rate limit) triggers retry."""
    mock_session = MagicMock()
    mock_session.get.return_value = MockResponse(text="", status_code=429)

    response = _fetch_page(mock_session, "https://example.com", retries=1, backoff=0.01)

    # Should retry and eventually return the 429 response
    assert mock_session.get.call_count > 1


# ------------------------------------------------------------
# _fetch_full_job_description Tests
# ------------------------------------------------------------


@patch("jobsai.utils.scrapers.duunitori._fetch_page")
def test_fetch_full_job_description_success(mock_fetch_page):
    """Test fetching full job description successfully."""
    html = """
    <div class="description">
        Full job description with lots of details about the position.
    </div>
    """
    mock_response = MockResponse(text=html, status_code=200)
    mock_fetch_page.return_value = mock_response

    mock_session = MagicMock()
    description = _fetch_full_job_description(
        mock_session, "https://duunitori.fi/job/123"
    )

    assert "Full job description" in description
    assert len(description) > 0


@patch("jobsai.utils.scrapers.duunitori._fetch_page")
def test_fetch_full_job_description_not_found(mock_fetch_page):
    """Test handling when job description is not found."""
    html = "<div>No description here</div>"
    mock_response = MockResponse(text=html, status_code=200)
    mock_fetch_page.return_value = mock_response

    mock_session = MagicMock()
    description = _fetch_full_job_description(
        mock_session, "https://duunitori.fi/job/123"
    )

    assert description == ""


@patch("jobsai.utils.scrapers.duunitori._fetch_page")
def test_fetch_full_job_description_non_200(mock_fetch_page):
    """Test handling non-200 status codes."""
    mock_response = MockResponse(text="", status_code=404)
    mock_fetch_page.return_value = mock_response

    mock_session = MagicMock()
    description = _fetch_full_job_description(
        mock_session, "https://duunitori.fi/job/123"
    )

    assert description == ""


# ------------------------------------------------------------
# scrape_duunitori Tests (with HTTP mocking)
# ------------------------------------------------------------


@patch("jobsai.utils.scrapers.duunitori._fetch_full_job_description")
@patch("jobsai.utils.scrapers.duunitori._fetch_page")
def test_scrape_duunitori_single_page(mock_fetch_page, mock_fetch_detail):
    """Test scraping a single page of results."""
    # Load fixture HTML
    page_html = load_fixture("duunitori_page_1.html")
    detail_html = load_fixture("duunitori_detail.html")

    # Mock responses: page 1 has jobs, page 2 is empty
    mock_fetch_page.side_effect = [
        MockResponse(text=page_html, status_code=200),  # Page 1
        MockResponse(text="<div>No results</div>", status_code=200),  # Page 2 empty
    ]
    mock_fetch_detail.return_value = "Full job description from detail page"

    results = scrape_duunitori("python developer", num_pages=2, deep_mode=True)

    assert len(results) > 0
    # Check that jobs have required fields
    for job in results:
        assert "title" in job
        assert "url" in job
        assert "source" in job
        assert job["source"] == "duunitori"
        # In deep mode, full_description should be present
        assert "full_description" in job


@patch("jobsai.utils.scrapers.duunitori._fetch_full_job_description")
@patch("jobsai.utils.scrapers.duunitori._fetch_page")
def test_scrape_duunitori_light_mode(mock_fetch_page, mock_fetch_detail):
    """Test that light mode (deep_mode=False) doesn't fetch job details."""
    page_html = load_fixture("duunitori_page_1.html")

    mock_fetch_page.side_effect = [
        MockResponse(text=page_html, status_code=200),
        MockResponse(text="<div>No results</div>", status_code=200),
    ]

    results = scrape_duunitori("python developer", num_pages=2, deep_mode=False)

    # In light mode, detail fetch should not be called
    mock_fetch_detail.assert_not_called()
    assert len(results) > 0
    # full_description should be None or empty in light mode
    for job in results:
        assert "full_description" in job
        assert job.get("full_description") is None or job.get("full_description") == ""


@patch("jobsai.utils.scrapers.duunitori._fetch_page")
def test_scrape_duunitori_pagination_stops(mock_fetch_page):
    """Test that pagination stops when no jobs are found."""
    page_html = load_fixture("duunitori_page_1.html")
    empty_html = load_fixture("duunitori_page_empty.html")

    mock_fetch_page.side_effect = [
        MockResponse(text=page_html, status_code=200),  # Page 1 has jobs
        MockResponse(text=empty_html, status_code=200),  # Page 2 empty
    ]

    results = scrape_duunitori("python developer", num_pages=10, deep_mode=False)

    # Should stop at page 2 when no jobs found
    assert len(results) > 0
    # Should have fetched page 1, then page 2 (which is empty, so stops)
    # The actual call count depends on implementation, but should be <= 2
    assert mock_fetch_page.call_count <= 2


@patch("jobsai.utils.scrapers.duunitori._fetch_page")
def test_scrape_duunitori_handles_non_200(mock_fetch_page):
    """Test that non-200 status codes stop scraping gracefully."""
    mock_fetch_page.return_value = MockResponse(text="", status_code=500)

    results = scrape_duunitori("python developer", num_pages=5, deep_mode=False)

    assert results == []


@patch("jobsai.utils.scrapers.duunitori._fetch_page")
def test_scrape_duunitori_cancellation_check(mock_fetch_page):
    """Test that cancellation check works during scraping."""
    cancellation_called = False

    def cancellation_check():
        nonlocal cancellation_called
        cancellation_called = True
        return True

    page_html = load_fixture("duunitori_page_1.html")
    mock_fetch_page.return_value = MockResponse(text=page_html, status_code=200)

    with pytest.raises(CancellationError):
        scrape_duunitori(
            "python developer",
            num_pages=5,
            deep_mode=False,
            cancellation_check=cancellation_check,
        )
    assert cancellation_called


@patch("jobsai.utils.scrapers.duunitori._fetch_page")
def test_scrape_duunitori_per_page_limit(mock_fetch_page):
    """Test that per_page_limit stops fetching when reached."""
    # Create HTML with multiple job cards
    page_html_multiple = """
    <div class="grid-sandbox">
        <div class="grid job-box job-box--lg">
            <h3 class="job-box__title">
                <a href="/tyopaikat/1" class="job-box__hover gtm-search-result" data-company="Company A">Job 1</a>
            </h3>
        </div>
        <div class="grid job-box job-box--lg">
            <h3 class="job-box__title">
                <a href="/tyopaikat/2" class="job-box__hover gtm-search-result" data-company="Company B">Job 2</a>
            </h3>
        </div>
        <div class="grid job-box job-box--lg">
            <h3 class="job-box__title">
                <a href="/tyopaikat/3" class="job-box__hover gtm-search-result" data-company="Company C">Job 3</a>
            </h3>
        </div>
        <div class="grid job-box job-box--lg">
            <h3 class="job-box__title">
                <a href="/tyopaikat/4" class="job-box__hover gtm-search-result" data-company="Company D">Job 4</a>
            </h3>
        </div>
        <div class="grid job-box job-box--lg">
            <h3 class="job-box__title">
                <a href="/tyopaikat/5" class="job-box__hover gtm-search-result" data-company="Company E">Job 5</a>
            </h3>
        </div>
        <div class="grid job-box job-box--lg">
            <h3 class="job-box__title">
                <a href="/tyopaikat/6" class="job-box__hover gtm-search-result" data-company="Company F">Job 6</a>
            </h3>
        </div>
    </div>
    """

    mock_fetch_page.return_value = MockResponse(
        text=page_html_multiple, status_code=200
    )

    results = scrape_duunitori(
        "python developer",
        num_pages=10,
        deep_mode=False,
        per_page_limit=5,
    )

    # Should stop when limit (5) is reached, even if more jobs are available
    assert len(results) <= 5
