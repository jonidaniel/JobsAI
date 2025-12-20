"""
Functions for scraping the Jobly job board.

This module provides a backward-compatible interface to the Jobly scraper.
The actual scraping logic is implemented in the unified base scraper, which uses
a configuration-driven approach to support multiple job boards (Duunitori and Jobly).

DESCRIPTION:
    1. When given a query, fetches the job detail page and extracts the full description for each listing (deep mode)
    2. Pagination limit default is 10 pages
    3. Returns a list of normalized job dicts (doesn't persist to disk)

URL SCHEME:
    Template:         https://www.jobly.fi/en/jobs?search={query_encoded}&page={page}
    Example:          https://www.jobly.fi/en/jobs?search=python-developer&page=2

HTML PARSING STRATEGY:
    Title:            .node__title
    Company:          .company-name, .company, [data-company], .employer
    Location:         .location, .job-location, [data-location], .city, .region
    URL:              a[href*='/jobs/'], a[href*='/job/']
    Published date:   .date, .published, .posted, [data-date], .job-date, time

Jobly's HTML may change; the parser uses several fallback selectors
If you see missed fields, inspect live HTML and tweak selectors
Select between light and deep mode
Light mode scrapes only listing cards, deep mode scrapes the job detail page
"""

from typing import Any, Callable, Dict, List, Optional

from jobsai.utils.scrapers.base import scrape_jobs
from jobsai.utils.scrapers.configs import JOBLY_CONFIG


def scrape_jobly(
    query: str,
    num_pages: int = 10,
    deep_mode: bool = True,
    session: Optional[Any] = None,
    per_page_limit: Optional[int] = None,
    cancellation_check: Optional[Callable[[], bool]] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch job listings from Jobly.

    This is a backward-compatible wrapper around the unified scraper.
    The actual scraping logic is in the base scraper module.

    Args:
        query: The search query string, e.g. "python developer".
        num_pages: The number of pages to crawl.
        deep_mode: If True, fetch each job's detail page to extract the full description.
        session: The requests.Session to reuse connections (recommended).
        per_page_limit: The optional cap on total listings (stops when reached).
        cancellation_check: Optional callable that returns True if the operation
            should be cancelled. Checked before each page fetch and before each
            job detail fetch in deep mode.

    Returns:
        List[Dict]: The list of normalized job dictionaries.

    Raises:
        CancellationError: If cancellation_check returns True during execution
    """
    return scrape_jobs(
        query=query,
        config=JOBLY_CONFIG,
        num_pages=num_pages,
        deep_mode=deep_mode,
        session=session,
        per_page_limit=per_page_limit,
        cancellation_check=cancellation_check,
    )
