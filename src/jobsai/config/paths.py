# ---------- PATHS ----------

from pathlib import Path

# ----- LOCAL PATHS -----

SKILL_PROFILES_PATH = Path("memory/vector_db/")
JOB_LISTINGS_RAW_PATH = Path("data/job_listings/raw/")
JOB_LISTINGS_SCORED_PATH = Path("data/job_listings/scored/")
REPORTS_PATH = Path("data/reports/")
LETTERS_PATH = Path("data/cover_letters/")

SKILL_PROFILES_PATH.mkdir(parents=True, exist_ok=True)
JOB_LISTINGS_RAW_PATH.mkdir(parents=True, exist_ok=True)
JOB_LISTINGS_SCORED_PATH.mkdir(parents=True, exist_ok=True)
REPORTS_PATH.mkdir(parents=True, exist_ok=True)
LETTERS_PATH.mkdir(parents=True, exist_ok=True)

# ----- URLS -----

HOST_URL_DUUNITORI = "https://duunitori.fi"
SEARCH_URL_BASE_DUUNITORI = (
    "https://duunitori.fi/tyopaikat/haku/{query_slug}?sivu={page}"
)
HOST_URL_JOBLY = "https://jobly.fi"
SEARCH_URL_BASE_JOBLY = "https://duunitori.fi/tyopaikat/search/{query_slug}?page={page}"
