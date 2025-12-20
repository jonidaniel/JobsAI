"""
Base Scraper Module - Unified Job Board Scraper.

This module contains the unified scraper logic that works with any job board
configuration. It handles pagination, cancellation checks, deep mode, and all
common scraping patterns.

The scraper is configuration-driven: pass a ScraperConfig object to customize
behavior for different job boards.
"""

import time
from typing import Any, Callable, Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from jobsai.utils.exceptions import CancellationError
from jobsai.utils.logger import get_logger
from jobsai.utils.scrapers.configs import ScraperConfig

logger = get_logger(__name__)


def scrape_jobs(
    query: str,
    config: ScraperConfig,
    num_pages: int = 10,
    deep_mode: bool = True,
    session: Optional[requests.Session] = None,
    per_page_limit: Optional[int] = None,
    cancellation_check: Optional[Callable[[], bool]] = None,
) -> List[Dict[str, Any]]:
    """
    Unified scraper that works with any job board configuration.

    This function contains all the common scraping logic (pagination, cancellation,
    deep mode, etc.) and uses the provided ScraperConfig for scraper-specific behavior
    (selectors, URL patterns, etc.).

    Args:
        query: The search query string, e.g. "python developer".
        config: ScraperConfig object with scraper-specific settings.
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
        session = requests.Session()
    session.headers.update(config.headers)

    # Encode query using scraper-specific encoder
    encoded_query = config.query_encoder(query)

    results = []
    total_fetched = 0

    # Iterate over pages
    for page in range(1, num_pages + 1):
        # Check for cancellation before fetching each page
        if cancellation_check and cancellation_check():
            logger.info(" %s scraping cancelled by user", config.name.capitalize())
            raise CancellationError("Pipeline cancelled during job search")

        # Build search URL using template
        # Handle different URL template formats:
        # - Duunitori uses {query_slug} and {page}
        # - Jobly uses {query_encoded} and {page}
        try:
            if "{query_slug}" in config.search_url_template:
                search_url = config.search_url_template.format(
                    query_slug=encoded_query, page=page
                )
            elif "{query_encoded}" in config.search_url_template:
                search_url = config.search_url_template.format(
                    query_encoded=encoded_query, page=page
                )
            else:
                # Fallback: try both
                search_url = config.search_url_template.format(
                    query_slug=encoded_query,
                    query_encoded=encoded_query,
                    page=page,
                )
        except KeyError as e:
            logger.error(" URL template format error for %s: %s", config.name, e)
            break

        logger.info(
            " Fetching %s search page: %s", config.name.capitalize(), search_url
        )

        # Fetch page with retry logic
        response = _fetch_page(session, search_url)

        if not response:
            logger.error(
                " Failed to fetch search page after all retries — stopping",
                extra={
                    "extra_fields": {
                        "job_board": config.name,
                        "page": page,
                        "query": query,
                        "url": search_url,
                        "issue": "All retry attempts failed - check _fetch_page logs for exception details",
                    }
                },
            )
            break
        if response.status_code != 200:
            logger.warning(
                " Non-200 status (%s) for %s — stopping",
                response.status_code,
                search_url,
                extra={
                    "extra_fields": {
                        "job_board": config.name,
                        "page": page,
                        "query": query,
                        "status_code": response.status_code,
                        "url": search_url,
                        "response_preview": (
                            response.text[:500] if response.text else None
                        ),
                    }
                },
            )
            break

        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Diagnostic logging for debugging selector issues
        html_length = len(response.text)
        html_preview = response.text[:500] if html_length > 500 else response.text

        # Check for common blocking/error indicators
        blocking_indicators = [
            "captcha",
            "blocked",
            "access denied",
            "please enable javascript",
            "cloudflare",
            "verify you are human",
        ]
        html_lower = response.text.lower()
        found_blocking = [
            indicator for indicator in blocking_indicators if indicator in html_lower
        ]

        if found_blocking:
            logger.warning(
                " Possible blocking detected on %s page %s",
                config.name.capitalize(),
                page,
                extra={
                    "extra_fields": {
                        "job_board": config.name,
                        "page": page,
                        "query": query,
                        "blocking_indicators": found_blocking,
                        "html_length": html_length,
                        "html_preview": html_preview,
                    }
                },
            )

        # Select job cards using scraper-specific selector
        job_cards = soup.select(config.job_card_selector)

        # Break if no results
        if not job_cards:
            # Log diagnostic information when no cards found
            logger.warning(
                " No job cards found on page %s for query '%s'",
                page,
                query,
                extra={
                    "extra_fields": {
                        "job_board": config.name,
                        "page": page,
                        "query": query,
                        "selector": config.job_card_selector,
                        "html_length": html_length,
                        "html_preview": html_preview,
                        "has_blocking_indicators": bool(found_blocking),
                        "blocking_indicators": found_blocking,
                    }
                },
            )
            break

        # Process each job card
        for job_card in job_cards:
            # Check for cancellation before processing each job
            if cancellation_check and cancellation_check():
                logger.info(" %s scraping cancelled by user", config.name.capitalize())
                raise CancellationError("Pipeline cancelled during job search")

            # Parse job card using scraper-specific selectors
            job = _parse_job_card(job_card, config)

            # Deep mode: fetch full description
            if deep_mode and job.get("url"):
                try:
                    detail = _fetch_full_job_description(session, job["url"], config)
                    job["full_description"] = detail if detail else ""
                    # Only log if description fetch failed (empty result)
                    if not detail:
                        logger.debug(
                            "Full description fetch returned empty",
                            extra={
                                "extra_fields": {
                                    "job_board": config.name,
                                    "job_url": job.get("url"),
                                }
                            },
                        )
                except Exception as e:
                    logger.warning(
                        "Error fetching detail",
                        extra={
                            "extra_fields": {
                                "job_board": config.name,
                                "job_url": job.get("url"),
                                "error": str(e),
                                "error_type": type(e).__name__,
                            }
                        },
                    )
                    job["full_description"] = ""
            else:
                job["full_description"] = ""

            # Add metadata
            job["query_used"] = query
            job["source"] = config.name
            results.append(job)
            total_fetched += 1

            # Break if reached per_page_limit
            if per_page_limit and total_fetched >= per_page_limit:
                logger.info(" Reached per_page_limit (%s). Stopping.", per_page_limit)
                return results

        # Add delay to avoid hammering the website
        delay = 0.8
        time.sleep(delay)

        # Break if fewer cards than threshold (likely no next page)
        if len(job_cards) < config.pagination_threshold:
            break

    logger.info(" Fetched %s listings for query '%s'", len(results), query)

    return results


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
        session: Current HTTP session
        url: URL to fetch
        retries: Number of retries
        backoff: Backoff multiplier for retries
        timeout: Request timeout

    Returns:
        Optional[requests.Response]: Response object if successful, None if all retries failed
    """
    last_response = None
    last_exception = None
    for attempt in range(1, retries + 1):
        try:
            response = session.get(url, timeout=timeout)
            last_response = response

            if response.status_code == 200:
                return response
            elif response.status_code in (429, 503):
                logger.warning(
                    " Rate-limited or service unavailable (status %s) for %s. Backing off",
                    response.status_code,
                    url,
                    extra={
                        "extra_fields": {
                            "url": url,
                            "status_code": response.status_code,
                            "attempt": attempt,
                        }
                    },
                )
                if attempt < retries:
                    time.sleep(backoff * attempt)
            else:
                logger.warning(
                    " Non-200 status %s for %s",
                    response.status_code,
                    url,
                    extra={
                        "extra_fields": {
                            "url": url,
                            "status_code": response.status_code,
                            "attempt": attempt,
                            "response_preview": (
                                response.text[:500] if response.text else None
                            ),
                        }
                    },
                )
                return response  # Return to allow caller to handle non-200
        except requests.RequestException as e:
            last_exception = e
            logger.warning(
                " Request failed (attempt %s/%s) for %s: %s",
                attempt,
                retries,
                url,
                str(e),
                extra={
                    "extra_fields": {
                        "url": url,
                        "attempt": attempt,
                        "max_retries": retries,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                },
                exc_info=True,  # Include full traceback
            )
            if attempt < retries:
                time.sleep(backoff * attempt)

    # Return last response if we have one (e.g., 429 after retries), otherwise None
    if last_response is None:
        logger.error(
            " All retry attempts failed for %s",
            url,
            extra={
                "extra_fields": {
                    "url": url,
                    "retries": retries,
                    "last_exception": str(last_exception) if last_exception else None,
                    "last_exception_type": (
                        type(last_exception).__name__ if last_exception else None
                    ),
                    "issue": "All retry attempts failed - no response received",
                }
            },
            exc_info=last_exception
            is not None,  # Include traceback if we have an exception
        )
    return last_response


def _parse_job_card(job_card: BeautifulSoup, config: ScraperConfig) -> Dict[str, Any]:
    """
    Parse a search-result job card into a partial job dictionary.

    Uses scraper-specific selectors from the config to extract job information.

    Args:
        job_card: The job card BeautifulSoup element
        config: ScraperConfig with selectors for this job board

    Returns:
        Dict: Dictionary with job information (title, company, location, url, etc.)
    """
    # Parse title
    title_tag = job_card.select_one(config.title_selector)
    title = title_tag.get_text(strip=True) if title_tag else ""
    if not title:
        logger.debug(
            "Title selector did not match",
            extra={
                "extra_fields": {
                    "job_board": config.name,
                    "selector": config.title_selector,
                }
            },
        )

    # Parse company (handle both text and data attributes)
    company_tag = job_card.select_one(config.company_selector)
    if company_tag:
        # Try data attribute first (Duunitori style)
        if company_tag.has_attr("data-company"):
            company = company_tag.get("data-company", "")
        else:
            # Fallback to text content (Jobly style)
            company = company_tag.get_text(strip=True)
    else:
        company = ""
        logger.debug(
            "Company selector did not match",
            extra={
                "extra_fields": {
                    "job_board": config.name,
                    "selector": config.company_selector,
                }
            },
        )

    # Parse location
    location_tag = job_card.select_one(config.location_selector)
    location = location_tag.get_text(strip=True) if location_tag else ""
    if not location:
        logger.debug(
            "Location selector did not match",
            extra={
                "extra_fields": {
                    "job_board": config.name,
                    "selector": config.location_selector,
                }
            },
        )

    # Parse URL
    url_tag = job_card.select_one(config.url_selector)
    if not url_tag:
        # For complex selectors like "a[href*='/jobs/']", try finding any matching link
        if config.url_selector.startswith("a["):
            import re

            url_tag = job_card.find("a", href=re.compile(r"/jobs/|/job/"))
        # Fallback to title link if it exists
        if not url_tag:
            url_tag = title_tag

    href = url_tag.get("href") if url_tag and url_tag.has_attr("href") else ""
    full_url = urljoin(config.host_url, href) if href else ""
    if not full_url:
        logger.debug(
            "URL selector did not match",
            extra={
                "extra_fields": {
                    "job_board": config.name,
                    "selector": config.url_selector,
                }
            },
        )

    # Parse published date (handle both text and datetime attribute)
    published_tag = (
        job_card.select_one(config.published_date_selector)
        if config.published_date_selector
        else None
    )
    if published_tag:
        if published_tag.has_attr("datetime"):
            published = published_tag.get("datetime", "")
        else:
            published = published_tag.get_text(strip=True)
    else:
        published = ""
        if config.published_date_selector:
            logger.debug(
                "Published date selector did not match",
                extra={
                    "extra_fields": {
                        "job_board": config.name,
                        "selector": config.published_date_selector,
                    }
                },
            )

    # Parse description snippet (optional)
    snippet = None
    if config.description_snippet_selector:
        snippet_tag = job_card.select_one(config.description_snippet_selector)
        snippet = snippet_tag.get_text(strip=True) if snippet_tag else None
        if not snippet:
            logger.debug(
                "Description snippet selector did not match",
                extra={
                    "extra_fields": {
                        "job_board": config.name,
                        "selector": config.description_snippet_selector,
                    }
                },
            )

    # Log extracted selector values only if there are issues (empty fields) or in DEBUG mode
    # This prevents log flooding when processing hundreds of job cards
    has_empty_fields = not title or not company or not location or not full_url
    if has_empty_fields:
        logger.warning(
            "Parsed job card with missing fields",
            extra={
                "extra_fields": {
                    "job_board": config.name,
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": full_url,
                    "published_date": published,
                    "title_length": len(title),
                    "company_length": len(company),
                    "location_length": len(location),
                }
            },
        )
    else:
        logger.info(
            "Parsed job card",
            extra={
                "extra_fields": {
                    "job_board": config.name,
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": full_url,
                    "published_date": published,
                    "title_length": len(title),
                    "company_length": len(company),
                    "location_length": len(location),
                }
            },
        )

    return {
        "title": title,
        "company": company,
        "location": location,
        "url": full_url,
        "description_snippet": snippet,
        "published_date": published,
    }


def _fetch_full_job_description(
    session: requests.Session, job_url: str, config: ScraperConfig, retries: int = 2
) -> str:
    """
    Fetch the job detail page and extract the full job description text.

    Uses scraper-specific selectors from the config, with optional fallback strategy.

    Args:
        session: Current HTTP session
        job_url: URL of the job to get full description of
        config: ScraperConfig with description selectors
        retries: Number of retries

    Returns:
        str: The full job description text, or empty string if not found
    """
    response = _fetch_page(session, job_url, retries=retries)

    if not response or response.status_code != 200:
        logger.debug(
            " Failed to fetch job detail: %s (status=%s)",
            job_url,
            getattr(response, "status_code", None),
        )
        return ""

    soup = BeautifulSoup(response.text, "html.parser")

    # Try each selector in order
    for i, selector in enumerate(config.full_description_selectors):
        description_tag = soup.select_one(selector)
        if description_tag:
            description = description_tag.get_text(strip=True)
            if description:
                # Only log in DEBUG mode to avoid flooding logs with hundreds of successful extractions
                logger.debug(
                    "Full description extracted",
                    extra={
                        "extra_fields": {
                            "job_board": config.name,
                            "job_url": job_url,
                            "selector_index": i,
                            "selector": selector,
                            "description_length": len(description),
                        }
                    },
                )
                return description
        else:
            logger.debug(
                "Selector did not match",
                extra={
                    "extra_fields": {
                        "job_board": config.name,
                        "job_url": job_url,
                        "selector_index": i,
                        "selector": selector,
                    }
                },
            )

    # Try fallback strategy if available
    if config.fallback_description_strategy:
        description = config.fallback_description_strategy(soup)
        if description:
            # Only log in DEBUG mode to avoid flooding logs
            logger.debug(
                "Full description extracted via fallback",
                extra={
                    "extra_fields": {
                        "job_board": config.name,
                        "job_url": job_url,
                        "description_length": len(description),
                    }
                },
            )
            return description

    # Log warning if no description found
    logger.warning(
        "No full description found",
        extra={
            "extra_fields": {
                "job_board": config.name,
                "job_url": job_url,
                "selectors_tried": len(config.full_description_selectors),
                "selectors": config.full_description_selectors,
            }
        },
    )

    return ""
