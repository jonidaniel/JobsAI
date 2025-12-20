"""
JobsAI HTTP Headers Configuration

This module defines HTTP headers used when scraping job boards.
Headers are configured to mimic browser requests and avoid blocking.

Supported job boards:
    - Duunitori: Finnish-focused headers with Finnish language preference
    - Jobly: English-focused headers with English language preference
"""

# ---------- HEADERS ----------

# ----- DUUNITORI -----

# HTTP headers for Duunitori job board scraping
# Configured to mimic a Chrome browser on Windows
HEADERS_DUUNITORI = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fi-FI,fi;q=0.9,en;q=0.8",  # Prefer Finnish, fallback to English
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Connection": "keep-alive",  # Reuse connections for better performance
}

# ----- JOBLY -----

# HTTP headers for Jobly job board scraping
# Configured to mimic a Chrome browser, prefers English content
HEADERS_JOBLY = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,fi;q=0.8",  # Prefer English, fallback to Finnish
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Connection": "keep-alive",  # Reuse connections for better performance
    "Referer": "https://www.jobly.fi/",  # Indicate we came from Jobly homepage
}
