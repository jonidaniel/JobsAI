# ---------- DUUNITORI SCRAPER ----------

# --- DESCRIPTION ---

# 1. When given a query, fetches the job detail page and extracts the full description for each listing (deep mode)
# 2. Pagination limit default is 10 pages
# 3. Returns a list of normalized job dicts (doesn't persist to disk)

# --- INPUT & OUTPUT ---

# Input:            A query, like 'python developer'
# Output:           {
#                     "title": "...",
#                     "company": "...",
#                     "location": "...",
#                     "url": "...",
#                     "published_date": "...",
#                     "description_snippet": "...",
#                     "source": "duunitori",
#                     "query_used": "python developer",
#                   }

# --- DUUNITORI.FI URL SCHEME ---

# Template:         https://duunitori.fi/tyopaikat/haku/<QUERY>?sivu=<PAGE>
# Example:          https://duunitori.fi/tyopaikat/haku/python-developer?sivu=2

# --- HTML PARSING STRATEGY ---

# Title:            <h3 class="job-box__title">
# Company:          <div class="job-box__employer">
# Location:         <div class="job-box__location">
# Link:             <a class="job-box__title-link" href="...">
# Published date:   <time datetime="...">

# Notes / Suggestions
# The scraper is intentionally defensive: Duunitori’s HTML may change; the parser uses several fallback selectors. If you see missed fields, inspect live HTML and tweak selectors.
# Deep mode causes one extra HTTP request per listing — plan API call rate/intervals accordingly.
# If you plan to run many queries frequently, add a persistent cache layer (disk/db) and respect robots.txt and Duunitori’s terms of service.
# You can easily switch to light mode by calling fetch_search_results(..., deep=False).

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

def fetch_search_results(
    query: str,
    num_pages: int = 10,
    deep_mode: bool = True,
    session: Optional[requests.Session] = None,
    per_page_limit: Optional[int] = None
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
    query_slug = slugify_query(query)

    results = []
    total_fetched = 0

    # Iterate over a number of webpages (10 by default)
    for page in range(1, num_pages + 1):
        # Inject URL with slugified query and page number
        search_url = SEARCH_URL_BASE_DUUNITORI.format(query_slug=query_slug, page=page)

        logger.info(" Fetching Duunitori search page: %s", search_url)

        # Get response safely
        response = safe_get(session, search_url)

        if not response:
            logger.warning(" Failed to fetch search page %s — stopping", search_url)
            break
        if response.status_code != 200:
            logger.warning(" Non-200 status (%s) for %s — stopping", response.status_code, search_url)
            break

        # Parse the HTML text with a HTML parser
        soup = BeautifulSoup(response.text, "html.parser")
        # Select CSS classes (here: job cards)
        cards = soup.select(".job-box, .job-list-item, .search-result__item, .job-card")

        # If no results on current page
        if not cards:
            logger.info(" No job cards found on page %s for query '%s' — stopping pagination", page, query)
            break

        # Iterate over job cards
        for card in cards:
            # Parse job card to a dictionary:
            # {
            # "title": title,
            # "company": company,
            # "location": location,
            # "url": full_url,
            # "description_snippet": snippet,
            # "published_date": published,
            # "source": "duunitori"
            # }
            job = parse_job_card(card)

            # If deep mode, and we have a URL
            if deep_mode and job.get("url"):
                try:
                    # Fetch full job description
                    detail = fetch_job_detail(session, job["url"])
                    if detail:
                        # Save the full job description under its own key
                        job["full_description"] = detail
                except Exception as e:
                    logger.warning(" Error fetching detail for %s: %s", job.get("url"), e)
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

def slugify_query(query: str) -> str:
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

    return quote_plus(q, safe="-") # Percent-encode remaining unsafe chars

def safe_get(
    session: requests.Session,
    url: str,
    retries: int = 3,
    backoff: float = 1.0,
    timeout: float = 10.0
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
        # Try to get response
        try:
            resp = session.get(url, timeout=timeout)
            # If OK, return response
            if resp.status_code == 200:
                return resp
            # If 'too many requests' or 'unavailable', wait a bit and continue
            elif resp.status_code in (429, 503):
                logger.warning(" Rate-limited or service unavailable (status %s) for %s. Backing off", resp.status_code, url)
                time.sleep(backoff * attempt)
            # If error, return response
            else:
                logger.debug(" Non-200 status %s for %s", resp.status_code, url)
                return resp  # return to allow caller to handle non-200
        except requests.RequestException as e:
            logger.warning(" Request failed (attempt %s/%s) for %s: %s", attempt, retries, url, e)
            time.sleep(backoff * attempt)
    return None

def parse_job_card(card: BeautifulSoup) -> Dict:
    """
    Parse a search-result job card into a partial job dict

    Defensive parsing: returns empty strings for missing fields

    Args:
        card: job card

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

    # Title and link
    title_tag = card.select_one(".job-box__title a, .job-box__title-link, h3 a")
    title = title_tag.get_text(strip=True) if title_tag else (card.select_one(".job-box__title").get_text(strip=True) if card.select_one(".job-box__title") else "")
    href = title_tag.get("href") if title_tag and title_tag.has_attr("href") else ""
    full_url = urljoin(HOST_URL_DUUNITORI, href) if href else ""

    # Company
    company_tag = card.select_one(".job-box__employer, .job-box__employer a")
    company = company_tag.get_text(strip=True) if company_tag else ""

    # Location
    location_tag = card.select_one(".job-box__location")
    location = location_tag.get_text(strip=True) if location_tag else ""

    # Description snippet — look for teaser or summary class
    snippet_tag = card.select_one(".job-box__teaser, .job-box__content__teaser, .job-box__excerpt")
    snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

    # Date
    time_tag = card.select_one("time")
    published = time_tag.get("datetime") if (time_tag and time_tag.has_attr("datetime")) else (time_tag.get_text(strip=True) if time_tag else "")

    return {
        "title": title,
        "company": company,
        "location": location,
        "url": full_url,
        "description_snippet": snippet,
        "published_date": published,
        "source": "duunitori"
    }

def fetch_job_detail(session: requests.Session, job_url: str, retries: int = 2) -> str:
    """
    Fetch the job detail page and attempt to extract the full job description text.

    Args:
        session: current HTTP session
        job_url: current job URL
        retries: number of retries to fetch job detail

    Returns:
        best_guess: best guess for full description div
        "": empty string on failure
    """

    # Get response safely
    response = safe_get(session, job_url, retries=retries)

    if not response or response.status_code != 200:
        logger.debug(" Failed to fetch job detail: %s (status=%s)", job_url, getattr(response, "status_code", None))
        return ""

    # Parse the HTML text with a HTML parser
    soup = BeautifulSoup(response.text, "html.parser")

    # Look for the main description container by guessing class names
    desc_candidates = soup.select(".job-body, .job__description, .job-description, .job-detail__content, .advert-content")

    # If no class was found, go to fallback
    if not desc_candidates:
        # Get all divs
        divs = soup.find_all("div")

        best_guess = ""
        longest = 0

        # Iterate over all divs on webpage
        for div in divs:
            # Extract all text
            txt = div.get_text(" ", strip=True) # If child nodes, use space as separator, also strip trailing whitespace
            # Find longest textual div
            if len(txt) > longest:
                longest = len(txt)
                best_guess = txt

        # return best_guess or ""
        return best_guess

    # Prefer the first candidate with enough text
    for cand in desc_candidates:
        text = cand.get_text(" ", strip=True)
        if len(text) > 50:
            return text

    # Fallback to concatenation
    return " ".join(c.get_text(" ", strip=True) for c in desc_candidates)
