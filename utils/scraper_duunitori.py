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

logger = logging.getLogger(__name__)

BASE_SEARCH_URL = "https://duunitori.fi/tyopaikat/haku/{query_slug}?sivu={page}"
BASE_HOST = "https://duunitori.fi"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fi-FI,fi;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Connection": "keep-alive"
}

def slugify_query(query: str) -> str:
    """
    Convert "python developer" -> "python-developer"

    Also encode special characters safely.
    """

    if not query:
        return ""
    # Replace whitespace with hyphens and remove unsafe chars
    q = re.sub(r"\s+", "-", query.strip().lower())
    # percent-encode remaining unsafe chars for URL path
    return quote_plus(q, safe="-")

def safe_get(session: requests.Session, url: str, retries: int = 3, backoff: float = 1.0, timeout: float = 10.0) -> Optional[requests.Response]:
    """
    asd
    """

    for attempt in range(1, retries + 1):
        try:
            resp = session.get(url, timeout=timeout)
            if resp.status_code == 200:
                return resp
            elif resp.status_code in (429, 503):
                logger.warning(" Rate-limited or service unavailable (status %s) for %s. Backing off.", resp.status_code, url)
                time.sleep(backoff * attempt)
            else:
                logger.debug(" Non-200 status %s for %s", resp.status_code, url)
                return resp  # return to allow caller to handle non-200
        except requests.RequestException as e:
            logger.warning(" Request failed (attempt %s/%s) for %s: %s", attempt, retries, url, e)
            time.sleep(backoff * attempt)
    return None

def parse_job_card(card: BeautifulSoup) -> Dict:
    """
    Parse a search-result job card into a partial job dict.

    Defensive parsing: returns empty strings for missing fields.
    """

    # Title and link
    title_tag = card.select_one(".job-box__title a, .job-box__title-link, h3 a")
    title = title_tag.get_text(strip=True) if title_tag else (card.select_one(".job-box__title").get_text(strip=True) if card.select_one(".job-box__title") else "")
    href = title_tag.get("href") if title_tag and title_tag.has_attr("href") else ""
    full_url = urljoin(BASE_HOST, href) if href else ""

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
        session: asd
        job_url: asd
        retries: asd

    Returns:
        An empty string on failure.
    """

    resp = safe_get(session, job_url, retries=retries)
    if not resp or resp.status_code != 200:
        logger.debug(" Failed to fetch job detail: %s (status=%s)", job_url, getattr(resp, "status_code", None))
        return ""

    soup = BeautifulSoup(resp.text, "html.parser")
    # Look for the main description container
    desc_candidates = soup.select(".job-body, .job__description, .job-description, .job-detail__content, .advert-content")
    if not desc_candidates:
        # fallback: find largest textual div inside the page
        divs = soup.find_all("div")
        best = ""
        max_len = 0
        for d in divs:
            txt = d.get_text(" ", strip=True)
            if len(txt) > max_len:
                max_len = len(txt)
                best = txt
        return best or ""

    # prefer the first candidate with enough text
    for cand in desc_candidates:
        text = cand.get_text(" ", strip=True)
        if len(text) > 50:
            return text
    # fallback to concatenation
    return " ".join(c.get_text(" ", strip=True) for c in desc_candidates)

def fetch_search_results(
    query: str,
    max_pages: int = 10,
    deep: bool = True,
    session: Optional[requests.Session] = None,
    headers: Optional[dict] = None,
    per_page_limit: Optional[int] = None
    ) -> List[Dict]:
    """
    Fetch job listings from Duunitori for the given query.

    Args:
        query: search query string, e.g. "python developer"
        max_pages: maximum number of pages to crawl (default 10)
        deep: if True, fetch each job's detail page to extract the full description
        session: requests.Session to reuse connections (recommended)
        headers: optional headers override
        per_page_limit: optional cap on total listings (stops when reached)

    Returns:
        List of normalized job dictionaries.
    """

    if session is None:
        session = requests.Session()
    session.headers.update(headers or DEFAULT_HEADERS)

    query_slug = slugify_query(query)
    results = []
    total_fetched = 0

    for page in range(1, max_pages + 1):
        search_url = BASE_SEARCH_URL.format(query_slug=query_slug, page=page)
        logger.info(" Fetching Duunitori search page: %s", search_url)
        resp = safe_get(session, search_url)
        if not resp:
            logger.warning(" Failed to fetch search page %s — stopping.", search_url)
            break
        if resp.status_code != 200:
            logger.warning(" Non-200 status (%s) for %s — stopping.", resp.status_code, search_url)
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        # find all job cards; multiple fallbacks
        cards = soup.select(".job-box, .job-list-item, .search-result__item, .job-card")
        if not cards:
            # No results on this page — likely end
            logger.info(" No job cards found on page %s for query '%s' — stopping pagination.", page, query)
            break

        for card in cards:
            job = parse_job_card(card)
            # If deep mode, and we have a URL, fetch full description
            if deep and job.get("url"):
                try:
                    detail = fetch_job_detail(session, job["url"])
                    if detail:
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

        # polite delay to avoid hammering the site
        time.sleep(0.8)

    logger.info(" Fetched %s listings for query '%s'", len(results), query)
    return results
