"""
JobsAI HTTP Headers Configuration

This module defines HTTP headers used when scraping job boards.
Headers are configured to mimic browser requests and avoid blocking.
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

# ----- INDEED -----

# HTTP headers for Indeed job board scraping
# Configured to mimic a modern Chrome browser with additional anti-detection headers
HEADERS_INDEED = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
    "Referer": "https://www.indeed.com/",
    "DNT": "1",  # Do Not Track
}
