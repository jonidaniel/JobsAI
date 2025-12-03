"""
JobsAI Path and URL Configuration

This module defines all file system paths and URL templates used throughout the system.
All directories are automatically created if they don't exist.
"""

# ---------- PATHS ----------

from pathlib import Path

# ----- LOCAL PATHS -----

# Path where skill profiles are stored
# Files are named with timestamp: {timestamp}_skill_profile.json
SKILL_PROFILE_PATH = Path("src/jobsai/memory/vector_db/")

# Path where raw job listings from scrapers are saved
# Files are named: {timestamp}_{job_board}_{query}.json
RAW_JOB_LISTING_PATH = Path("src/jobsai/data/job_listings/raw/")

# Path where scored job listings are saved
# Files are named: {timestamp}_scored_jobs.json
SCORED_JOB_LISTING_PATH = Path("src/jobsai/data/job_listings/scored/")

# Path where job analyses are saved
# Files are named: {timestamp}_job_analysis.txt
JOB_ANALYSIS_PATH = Path("src/jobsai/data/job_analyses/")

# Path where generated cover letter documents are saved
# Files are named: {timestamp}_cover_letter.docx
COVER_LETTER_PATH = Path("src/jobsai/data/cover_letters/")

# Create all directories if they don't exist
# This ensures the system works even on first run
SKILL_PROFILE_PATH.mkdir(parents=True, exist_ok=True)
RAW_JOB_LISTING_PATH.mkdir(parents=True, exist_ok=True)
SCORED_JOB_LISTING_PATH.mkdir(parents=True, exist_ok=True)
JOB_ANALYSIS_PATH.mkdir(parents=True, exist_ok=True)
COVER_LETTER_PATH.mkdir(parents=True, exist_ok=True)

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
