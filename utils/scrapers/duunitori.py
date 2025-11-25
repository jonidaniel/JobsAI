# ---------- DUUNITORI SCRAPER ----------

# fetch_duunitori_results
# _slugify_query
# _safe_get
# _parse_job_card
# _fetch_job_detail

# --- DESCRIPTION ---

# 1. When given a query, fetches the job detail page and extracts the full description for each listing (deep mode)
# 2. Pagination limit default is 10 pages
# 3. Returns a list of normalized job dicts (doesn't persist to disk)

# Duunitori’s HTML may change; the parser uses several fallback selectors
# If you see missed fields, inspect live HTML and tweak selectors
# Deep mode causes one extra HTTP request per listing — plan API call rate/intervals accordingly
# If you plan to run many queries frequently, add a persistent cache layer (disk/db) and respect robots.txt and Duunitori’s terms of service
# You can easily switch to light mode by calling fetch_duunitori_results(..., deep=False)

# --- URL SCHEME ---

# Template:         https://duunitori.fi/tyopaikat/haku/<QUERY>?sivu=<PAGE>
# Example:          https://duunitori.fi/tyopaikat/haku/python-developer?sivu=2

# --- HTML PARSING STRATEGY ---

# Title:            <h3 class="job-box__title">
# Company:          <div class="job-box__employer">
# Location:         <div class="job-box__location">
# URL:              <a class="job-box__title-link" href="...">
# Published date:   <time datetime="...">

import time
import logging
import requests
import re
from typing import List, Dict, Optional
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup

from config.paths import HOST_URL_DUUNITORI, SEARCH_URL_BASE_DUUNITORI
from config.headers import HEADERS_DUUNITORI

logger = logging.getLogger(__name__)


def fetch_duunitori_results(
    query: str,
    num_pages: int = 10,
    deep_mode: bool = True,
    session: Optional[requests.Session] = None,
    per_page_limit: Optional[int] = None,
) -> List[Dict]:
    """
    Fetch job listings from Duunitori for the given query.

    Args:
        query: search query string, e.g. "python developer"
        num_pages: number of pages to crawl
        deep_mode: if True, fetch each job's detail page to extract the full description
        session: requests.Session to reuse connections (recommended)
        per_page_limit: optional cap on total listings (stops when reached)

    Returns:
        results: list of normalized job dictionaries
    """

    if session is None:
        # Create HTTP session
        session = requests.Session()
    # Update default headers
    session.headers.update(HEADERS_DUUNITORI)

    # Make query URL compliant
    query_slug = _slugify_query(query)

    results = []
    total_fetched = 0

    # Iterate over a number of webpages (10 by default)
    for page in range(1, num_pages + 1):
        # Inject URL with slugified query and page number
        search_url = SEARCH_URL_BASE_DUUNITORI.format(query_slug=query_slug, page=page)

        logger.info(" Fetching Duunitori search page: %s", search_url)

        # Get response safely
        response = _safe_get(session, search_url)

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

        # Select all job cards (ignore cards in 'Duunitori suosittelee' section)
        cards = soup.select(
            ".grid-sandbox.grid-sandbox--tight-bottom.grid-sandbox--tight-top .grid.grid--middle.job-box.job-box--lg"
        )

        # If no results on current page
        if not cards:
            logger.info(
                " No job cards found on page %s for query '%s' — stopping pagination",
                page,
                query,
            )
            break

        # Iterate over job cards
        for card in cards:
            job = _parse_job_card(card)

            # If in deep mode, and we have a URL
            if deep_mode and job.get("url"):
                try:
                    # Fetch full job description
                    detail = _fetch_job_detail(session, job["url"])

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

    logger.info(" Fetched %s listings for query '%s'", len(results), query)

    return results


def _slugify_query(query: str) -> str:
    """
    Make query URL compliant (e.g. turn 'python developer' into 'python-developer').

    Also encode special characters safely.

    Args:
        query: query to be slugified

    Returns:
        "": if there wasn't a query
        quote_plus(q, safe="-"): URL compliant query
    """

    if not query:
        return ""

    # Replace whitespace with hyphens and remove unsafe chars
    q = re.sub(r"\s+", "-", query.strip().lower())

    return quote_plus(q, safe="-")  # Percent-encode remaining unsafe chars


def _safe_get(
    session: requests.Session,
    url: str,
    retries: int = 3,
    backoff: float = 1.0,
    timeout: float = 10.0,
) -> Optional[requests.Response]:
    """
    asd

    Args:
        session: current HTTP session
        url: search URL
        retries: number of search retries
        backoff:
        timeout: time to timeout

    Returns:
        resp:
        None:
    """

    # Iterate 3 times (by default)
    for attempt in range(1, retries + 1):
        try:
            # Get response
            resp = session.get(url, timeout=timeout)
            # If OK, return response
            if resp.status_code == 200:
                return resp
            # If 'too many requests' or 'unavailable', wait a bit and continue
            elif resp.status_code in (429, 503):
                logger.warning(
                    " Rate-limited or service unavailable (status %s) for %s. Backing off",
                    resp.status_code,
                    url,
                )
                time.sleep(backoff * attempt)
            # If error, return response
            else:
                logger.debug(" Non-200 status %s for %s", resp.status_code, url)
                return resp  # return to allow caller to handle non-200
        except requests.RequestException as e:
            logger.warning(
                " Request failed (attempt %s/%s) for %s: %s", attempt, retries, url, e
            )
            time.sleep(backoff * attempt)
    return None


def _parse_job_card(card: BeautifulSoup) -> Dict:
    """
    Parse a search-result job card into a partial job dict

    Defensive parsing: returns empty strings for missing fields

    Args:
        card: the job card

    Returns:
        {
          "title": title,
          "company": company,
          "location": location,
          "url": full_url,
          "description_snippet": snippet,
          "published_date": published,
          "source": "duunitori"
        }:
    """

    # Title
    title_tag = card.select_one(".job-box__title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # Company
    job_tag = card.select_one(".job-box__hover.gtm-search-result")
    company = (
        job_tag.get("data-company")
        if job_tag and job_tag.has_attr("data-company")
        else ""
    )

    # Location
    location_tag = card.select_one(".job-box__job-location")
    location = (
        location_tag.get_text(strip=True)
        if location_tag
        else (
            card.select_one(".job-box__job-location").get_text(strip=True)
            if card.select_one(".job-box__job-location")
            else ""
        )
    )

    # URL
    href = job_tag.get("href") if job_tag and job_tag.has_attr("href") else ""
    full_url = urljoin(HOST_URL_DUUNITORI, href) if href else ""

    # Description
    snippet = ""

    # Published
    published_tag = card.select_one(".job-box__job-posted")
    published = (
        published_tag.get_text(strip=True)
        if published_tag
        else (
            card.select_one(".job-box__job-posted").get_text(strip=True)
            if card.select_one(".job-box__job-posted")
            else ""
        )
    )

    # Category
    category = (
        job_tag.get("data-category")
        if job_tag and job_tag.has_attr("data-category")
        else ""
    )

    return {
        "title": title,
        "company": company,
        "location": location,
        "url": full_url,
        "description_snippet": snippet,
        "published_date": published,
        "source": "duunitori",
    }


def _fetch_job_detail(session: requests.Session, job_url: str, retries: int = 2) -> str:
    """
    Fetch the job detail page and attempt to extract the full job description text.

    Args:
        session: current HTTP session
        job_url: current job URL
        retries: number of retries to fetch job detail

    Returns:
        description: the full job description
        best_guess: best guess for full description div
        "": empty string on failure
    """

    # Get response safely
    response = _safe_get(session, job_url, retries=retries)

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
    description_tag = soup.select_one(".description, .description--jobentry")
    description = description_tag.get_text(strip=True) if description_tag else ""
    if description:
        return description

    # --- FALLBACK SECTION ---

    # # Look for the main description container by guessing class names
    # # desc_candidates = soup.select(".job-body, .job__description, .job-description, .job-detail__content, .advert-content")
    # desc_candidates = soup.select(".gtm-apply-clicks, .description, .description--jobentry, .job-body, .job__description, .job-description, .job-detail__content, .advert-content")

    # # If no class was found, go to fallback
    # if not desc_candidates:
    #     # Get all divs
    #     divs = soup.find_all("div")

    #     best_guess = ""
    #     longest = 0

    #     # Iterate over all divs on webpage
    #     for div in divs:
    #         # Extract all text
    #         txt = div.get_text(" ", strip=True) # If child nodes, use space as separator, also strip trailing whitespace
    #         # Find longest textual div
    #         if len(txt) > longest:
    #             longest = len(txt)
    #             best_guess = txt

    #     # return best_guess or ""
    #     return best_guess

    # # Prefer the first candidate with enough text
    # for cand in desc_candidates:
    #     text = cand.get_text(" ", strip=True)
    #     if len(text) > 50:
    #         return text

    # # Fallback to concatenation
    # return " ".join(c.get_text(" ", strip=True) for c in desc_candidates)
