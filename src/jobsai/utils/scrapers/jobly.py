"""
Functions for scraping the Jobly job board.

    scrape_jobly
    _fetch_page                 (internal use only)
    _parse_job_card             (internal use only)
    _fetch_full_job_description (internal use only)

DESCRIPTION:
    1. When given a query, fetches the job detail page and extracts the full description for each listing (deep mode)
    2. Pagination limit default is 10 pages
    3. Returns a list of normalized job dicts (doesn't persist to disk)

URL SCHEME:
    Template:         https://www.jobly.fi/en/jobs?search=<QUERY>&page=<PAGE>
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
You can easily switch to light mode by setting DEEP_MODE=False in /config/settings.py
"""

import time
import logging
import requests
import re
from typing import List, Dict, Optional, Callable
from urllib.parse import urljoin, quote_plus

from bs4 import BeautifulSoup

from jobsai.config.headers import HEADERS_JOBLY
from jobsai.utils.exceptions import CancellationError
from jobsai.config.paths import (
    HOST_URL_JOBLY,
    SEARCH_URL_BASE_JOBLY,
)

logger = logging.getLogger(__name__)


# ------------------------------
# Public interface
# ------------------------------
def scrape_jobly(
    query: str,
    num_pages: int = 10,
    deep_mode: bool = True,
    session: Optional[requests.Session] = None,
    per_page_limit: Optional[int] = None,
    cancellation_check: Optional[Callable[[], bool]] = None,
) -> List[Dict]:
    """
    Fetch job listings from Jobly.

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

    if session is None:
        # Create HTTP session
        session = requests.Session()
    # Update default headers
    session.headers.update(HEADERS_JOBLY)

    # URL-encode query (handle spaces and special characters)
    query_encoded = quote_plus(query.strip())

    results = []
    total_fetched = 0

    # Iterate over a number of webpages (10 by default)
    for page in range(1, num_pages + 1):
        # Check for cancellation before fetching each page
        if cancellation_check and cancellation_check():
            logger.info(" Jobly scraping cancelled by user")
            raise CancellationError("Pipeline cancelled during job search")

        # Build search URL with query and page number
        search_url = SEARCH_URL_BASE_JOBLY.format(
            query_encoded=query_encoded, page=page
        )

        logger.info(" Fetching Jobly search page: %s", search_url)

        # Get response from the search URL
        response = _fetch_page(session, search_url)
        if not response:
            logger.warning(" Failed to fetch search page %s — stopping", search_url)
            break
        if response.status_code != 200:
            logger.warning(
                " Non-200 status (%s) for %s — stopping",
                response.status_code,
                search_url,
            )
            break
        # Parse the HTML text with a HTML parser
        soup = BeautifulSoup(response.text, "html.parser")

        # Select all job cards
        job_cards = soup.select(".job__content.clearfix")

        # If no results on current page
        if not job_cards:
            logger.info(
                " No job cards found on page %s for query '%s' — stopping pagination",
                page,
                query,
            )
            break

        # Iterate over job cards on current page
        for job_card in job_cards:
            # Check for cancellation before processing each job (especially important in deep mode)
            if cancellation_check and cancellation_check():
                logger.info(" Jobly scraping cancelled by user")
                raise CancellationError("Pipeline cancelled during job search")

            job = _parse_job_card(job_card)

            # If in deep mode, and we have a URL
            if deep_mode and job.get("url"):
                try:
                    # Fetch full job description
                    detail = _fetch_full_job_description(session, job["url"])

                    if detail:
                        # Save the full job description under its own key
                        job["full_description"] = detail
                except Exception as e:
                    logger.warning(
                        " Error fetching detail for %s: %s", job.get("url"), e
                    )
                    job["full_description"] = ""
            else:
                job["full_description"] = ""

            # Metadata enrichment
            job["query_used"] = query
            results.append(job)
            total_fetched += 1

            if per_page_limit and total_fetched >= per_page_limit:
                logger.info(" Reached per_page_limit (%s). Stopping.", per_page_limit)
                return results

        # Add delay to avoid hammering the website
        time.sleep(0.8)

        # Break if less than expected job cards on page (likely no next page)
        if len(job_cards) < 10:
            break

    logger.info(" Fetched %s listings for query '%s'", len(results), query)

    return results


# ------------------------------
# Internal functions
# ------------------------------


def _fetch_page(
    session: requests.Session,
    url: str,
    retries: int = 3,
    backoff: float = 1.0,
    timeout: float = 10.0,
) -> Optional[requests.Response]:
    """
    Fetch a page with retry logic and error handling.

    Args:
        session: The requests.Session to reuse connections (recommended).
        url: The URL to fetch.
        retries: Number of search retries.
        backoff: Backoff multiplier for retries.
        timeout: Time to timeout.

    Returns:
        Optional[requests.Response]: Response object if successful, None if all retries failed
    """

    # Iterate 3 times (by default)
    for attempt in range(1, retries + 1):
        try:
            # Get response
            response = session.get(url, timeout=timeout)
            # If OK, return response
            if response.status_code == 200:
                return response
            # If 'too many requests' or 'unavailable', wait a bit and continue
            elif response.status_code in (429, 503):
                logger.warning(
                    " Rate-limited or service unavailable (status %s) for %s. Backing off",
                    response.status_code,
                    url,
                )
                time.sleep(backoff * attempt)
            # If error, return response
            else:
                logger.debug(" Non-200 status %s for %s", response.status_code, url)
                return response  # return to allow caller to handle non-200
        except requests.RequestException as e:
            logger.warning(
                " Request failed (attempt %s/%s) for %s: %s", attempt, retries, url, e
            )
            time.sleep(backoff * attempt)
    return None


def _parse_job_card(job_card: BeautifulSoup) -> Dict:
    """
    Parse a search-result job card into a partial job dict

    Defensive parsing: returns empty strings for missing fields

    Args:
        job_card (BeautifulSoup): The job card BeautifulSoup element.

    Returns:
        Dict: The dictionary with job information.
    """

    # Parse title from job card
    title_tag = job_card.select_one(".node__title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # Parse company from job card
    company_tag = job_card.select_one(
        ".company-name, .company, [data-company], .employer"
    )
    company = (
        company_tag.get_text(strip=True)
        if company_tag
        else (
            company_tag.get("data-company")
            if company_tag and hasattr(company_tag, "get")
            else ""
        )
    )

    # Parse location from job card
    location_tag = job_card.select_one(
        ".location, .job-location, [data-location], .city, .region"
    )
    location = location_tag.get_text(strip=True) if location_tag else ""

    # Parse URL from job card
    # Try to find link to job detail page
    url_tag = (
        job_card.select_one("a[href*='/jobs/'], a[href*='/job/']")
        or job_card.find("a", href=re.compile(r"/jobs/|/job/"))
        or title_tag  # Fallback to title link if it exists
    )
    href = url_tag.get("href") if url_tag and url_tag.has_attr("href") else ""
    full_url = urljoin(HOST_URL_JOBLY, href) if href else ""

    # Parse published date from job card
    # Try multiple selectors for date
    published_tag = job_card.select_one(
        ".date, .published, .posted, [data-date], .job-date, time"
    )
    published = (
        published_tag.get_text(strip=True)
        if published_tag
        else (
            published_tag.get("datetime")
            if published_tag and published_tag.has_attr("datetime")
            else ""
        )
    )

    # Parse description snippet if available
    snippet_tag = job_card.select_one(
        ".description, .snippet, .summary, .job-description"
    )
    snippet = snippet_tag.get_text(strip=True) if snippet_tag else None

    return {
        "title": title,
        "company": company,
        "location": location,
        "url": full_url,
        "description_snippet": snippet,
        "published_date": published,
        "source": "jobly",
    }


def _fetch_full_job_description(
    session: requests.Session, job_url: str, retries: int = 2
) -> str:
    """
    Fetch the job detail page and attempt to extract the full job description text.

    Args:
        session: The requests.Session to reuse connections (recommended).
        job_url: The URL of the job to get full description of.
        retries: Number of retries to fetch full description.

    Returns:
        str: The full job description text, or an empty string if the description is not found.
    """

    # Get response safely
    response = _fetch_page(session, job_url, retries=retries)

    if not response or response.status_code != 200:
        logger.debug(
            " Failed to fetch job detail: %s (status=%s)",
            job_url,
            getattr(response, "status_code", None),
        )
        return ""

    # Parse the HTML text with a HTML parser
    soup = BeautifulSoup(response.text, "html.parser")

    # Find the full job description
    # Try multiple selectors for job description
    description_tag = soup.select_one(
        ".job-description, .description, .job-details, .content, .job-content, main article, [role='article']"
    )
    description = description_tag.get_text(strip=True) if description_tag else ""

    if description:
        return description

    # Fallback: look for the longest text block (likely the description)
    # This is a last resort if standard selectors don't work
    divs = soup.find_all(["div", "section", "article"])
    best_guess = ""
    longest = 0

    for div in divs:
        text_content = div.get_text(" ", strip=True)
        # Look for divs with substantial text (likely descriptions)
        if len(text_content) > longest and len(text_content) > 100:
            longest = len(text_content)
            best_guess = text_content

    return best_guess
