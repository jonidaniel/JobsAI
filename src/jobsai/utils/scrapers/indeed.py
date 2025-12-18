"""
Functions for scraping the Indeed job board.

This module provides a backward-compatible interface to the Indeed scraper.
The actual scraping logic is implemented in the unified base scraper, which uses
a configuration-driven approach to support multiple job boards.

DESCRIPTION:
    1. When given a query, fetches the job detail page and extracts the full description for each listing (deep mode)
    2. Returns a list of normalized job dicts (doesn't persist to disk)

URL SCHEME:
    Template:         https://www.indeed.com/jobs?q={query_slug}&start={start}
    Example:          https://www.indeed.com/jobs?q=python+developer&start=10

HTML PARSING STRATEGY:
    Title:            .job-title
    Company:          .company
    Location:         .location
    URL:              .job-title a
    Published date:   .date

Indeed's HTML may change; the parser uses several fallback selectors
If you see missed fields, inspect live HTML and tweak selectors
Select between light and deep mode
Light mode scrapes only listing cards, deep mode scrapes the job detail page
"""

from typing import Any, Callable, Dict, List, Optional

from jobsai.utils.scrapers.base import scrape_jobs
from jobsai.utils.scrapers.configs import INDEED_CONFIG


def scrape_indeed(
    query: str,
    num_pages: int = 10,
    deep_mode: bool = True,
    session: Optional[Any] = None,
    per_page_limit: Optional[int] = None,
    cancellation_check: Optional[Callable[[], bool]] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch job listings from Indeed.

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
        config=INDEED_CONFIG,
        num_pages=num_pages,
        deep_mode=deep_mode,
        session=session,
        per_page_limit=per_page_limit,
        cancellation_check=cancellation_check,
    )
