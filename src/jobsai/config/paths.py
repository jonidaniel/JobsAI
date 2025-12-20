"""
JobsAI Path and URL Configuration.

This module defines all file system paths and URL templates used throughout the system.
It handles environment-specific path configuration (Lambda vs local development) and
automatically creates required directories on first import.

Path Configuration:
    - Lambda: Uses /tmp/jobsai for writable storage (Lambda's only writable location)
    - Local: Uses src/jobsai for development (relative to project root)

Detection:
    - Checks for LAMBDA_TASK_ROOT environment variable to detect Lambda environment
    - Falls back to local paths if not in Lambda

Directory Structure:
    - data/job_listings/raw/: Raw job listings from scrapers (JSON files)
    - data/job_listings/scored/: Scored job listings (JSON files)
    - data/job_analyses/: Job analyses (text files)
    - data/cover_letters/: Generated cover letter documents (DOCX files)

URL Templates:
    - Duunitori: Search URL template with query slug and page number
      Format: https://duunitori.fi/tyopaikat/haku/{query_slug}?sivu={page}
    - Jobly: Search URL template with encoded query and page number
      Format: https://www.jobly.fi/en/jobs?search={query_encoded}&page={page}

Note:
    All directories are created automatically on module import. In Lambda, directory
    creation may fail silently if /tmp is full, but this is logged as a warning.
"""

# ---------- PATHS ----------

from pathlib import Path

# ----- LOCAL PATHS -----

# Lambda uses /tmp for writable storage (limited to 512MB-10GB depending on config)
# For local development, use src/jobsai paths
# For Lambda, use /tmp paths
import os

# Check if running in Lambda (Lambda sets LAMBDA_TASK_ROOT)
IS_LAMBDA = os.environ.get("LAMBDA_TASK_ROOT") is not None

if IS_LAMBDA:
    # Lambda environment: use /tmp for writable storage
    BASE_PATH = Path("/tmp/jobsai")
else:
    # Local development: use src/jobsai paths
    BASE_PATH = Path("src/jobsai")

# Path where raw job listings from scrapers are saved
# Files are named: {timestamp}_{job_board}_{query}.json
RAW_JOB_LISTING_PATH = BASE_PATH / "data" / "job_listings" / "raw"

# Path where scored job listings are saved
# Files are named: {timestamp}_scored_jobs.json
SCORED_JOB_LISTING_PATH = BASE_PATH / "data" / "job_listings" / "scored"

# Path where job analyses are saved
# Files are named: {timestamp}_job_analysis.txt
JOB_ANALYSIS_PATH = BASE_PATH / "data" / "job_analyses"

# Path where generated cover letter documents are saved
# Files are named: {timestamp}_cover_letter.docx
COVER_LETTER_PATH = BASE_PATH / "data" / "cover_letters"

# Create all directories if they don't exist
# This ensures the system works even on first run
# Note: In Lambda, this will create directories in /tmp (writable)
# In local dev, this will create directories in src/jobsai
try:
    RAW_JOB_LISTING_PATH.mkdir(parents=True, exist_ok=True)
    SCORED_JOB_LISTING_PATH.mkdir(parents=True, exist_ok=True)
    JOB_ANALYSIS_PATH.mkdir(parents=True, exist_ok=True)
    COVER_LETTER_PATH.mkdir(parents=True, exist_ok=True)
except OSError as e:
    # Log error but don't fail - directories might already exist or be read-only
    # In Lambda, /tmp should always be writable
    from jobsai.utils.logger import get_logger

    logger = get_logger(__name__)
    logger.warning(
        "Could not create directory",
        extra={"extra_fields": {"error": str(e), "error_type": type(e).__name__}},
    )

# ----- URLS -----

# Duunitori job board URLs
HOST_URL_DUUNITORI = "https://duunitori.fi"
# Search URL template for Duunitori
# {query_slug}: URL-encoded search query (e.g., "python-developer")
# {page}: Page number (1-based)
SEARCH_URL_BASE_DUUNITORI = (
    "https://duunitori.fi/tyopaikat/haku/{query_slug}?sivu={page}"
)

# Jobly job board URLs
HOST_URL_JOBLY = "https://www.jobly.fi"
# Search URL template for Jobly
# {query_encoded}: URL-encoded search query (e.g., "python+developer")
# {page}: Page number (1-based)
SEARCH_URL_BASE_JOBLY = (
    "https://www.jobly.fi/en/jobs?search={query_encoded}&page={page}"
)
