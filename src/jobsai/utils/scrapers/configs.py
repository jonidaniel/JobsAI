"""
Scraper Configuration Module.

Defines configuration dataclasses and pre-configured settings for each job board scraper.
This allows the unified scraper to work with different job boards by simply changing
the configuration.

Currently supports:
    - Duunitori: Finnish job board (duunitori.fi)
    - Jobly: Finnish job board (jobly.fi)
"""

import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional
from urllib.parse import quote_plus

from jobsai.config.headers import HEADERS_DUUNITORI, HEADERS_JOBLY
from jobsai.config.paths import (
    HOST_URL_DUUNITORI,
    HOST_URL_JOBLY,
    SEARCH_URL_BASE_DUUNITORI,
    SEARCH_URL_BASE_JOBLY,
)


@dataclass
class ScraperConfig:
    """Configuration for a job board scraper.

    Contains all scraper-specific settings including URL templates, CSS selectors,
    headers, and encoding functions. This allows the unified scraper to work with
    any job board by simply changing the configuration.
    """

    # Basic identification
    name: str  # "duunitori" or "jobly"
    host_url: str
    search_url_template: str
    headers: Dict[str, str]

    # Job card selection
    job_card_selector: str
    pagination_threshold: int  # Stop pagination if fewer cards found

    # Query encoding function
    query_encoder: Callable[[str], str]

    # Field selectors for parsing job cards
    title_selector: str
    company_selector: str
    location_selector: str
    url_selector: str
    published_date_selector: Optional[str]
    # Full description selectors (for deep mode) - required, must come before optional fields
    full_description_selectors: List[str]
    # Optional fields (must come after required fields)
    description_snippet_selector: Optional[str] = None
    fallback_description_strategy: Optional[Callable] = None


def _duunitori_query_encoder(query: str) -> str:
    """Encode query for Duunitori: slugify then URL-encode."""
    slugified_query = re.sub(r"\s+", "-", query.strip().lower())
    return quote_plus(slugified_query, safe="-")


def _jobly_query_encoder(query: str) -> str:
    """Encode query for Jobly: simple URL-encode."""
    return quote_plus(query.strip())


# Duunitori scraper configuration
DUUNITORI_CONFIG = ScraperConfig(
    name="duunitori",
    host_url=HOST_URL_DUUNITORI,
    search_url_template=SEARCH_URL_BASE_DUUNITORI,
    headers=HEADERS_DUUNITORI,
    job_card_selector=".grid-sandbox.grid-sandbox--tight-bottom.grid-sandbox--tight-top .grid.grid--middle.job-box.job-box--lg",
    pagination_threshold=20,
    query_encoder=_duunitori_query_encoder,
    title_selector=".job-box__title",
    company_selector=".job-box__hover.gtm-search-result",
    location_selector=".job-box__job-location",
    url_selector=".job-box__hover.gtm-search-result",
    published_date_selector=".job-box__job-posted",
    description_snippet_selector=None,
    full_description_selectors=[
        ".gtm-apply-clicks.description.description--jobentry",
    ],
    fallback_description_strategy=None,
)

# Jobly scraper configuration
JOBLY_CONFIG = ScraperConfig(
    name="jobly",
    host_url=HOST_URL_JOBLY,
    search_url_template=SEARCH_URL_BASE_JOBLY,
    headers=HEADERS_JOBLY,
    # job_card_selector=".job__content.clearfix",
    job_card_selector=".views-row",
    pagination_threshold=10,
    query_encoder=_jobly_query_encoder,
    title_selector=".node__title a",
    company_selector=".recruiter-company-profile-job-organization a",
    location_selector=".location span",
    url_selector=".node__title a",
    published_date_selector=".date",
    description_snippet_selector=None,
    # full_description_selectors=[".field__item.even"],
    full_description_selectors=[
        ".field.field--name-body.field--type-text-with-summary.field--label-hidden"
    ],
    fallback_description_strategy=None,
)
