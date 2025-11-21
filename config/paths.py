# ---------- PATHS ----------

from pathlib import Path

# ----- LOCAL PATHS -----

SKILL_PROFILE_PATH = Path("memory/vector_db/skill_profile.json")
JOB_LISTINGS_RAW_PATH = Path("data/job_listings/raw/")
JOB_LISTINGS_SCORED_PATH = Path("data/job_listings/scored/")
REPORTS_PATH = Path("data/reports/")

SKILL_PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
JOB_LISTINGS_RAW_PATH.mkdir(parents=True, exist_ok=True)
JOB_LISTINGS_SCORED_PATH.mkdir(parents=True, exist_ok=True)
REPORTS_PATH.mkdir(parents=True, exist_ok=True)

# ----- URLS -----

HOST_URL_DUUNITORI = "https://duunitori.fi"
SEARCH_URL_BASE_DUUNITORI = "https://duunitori.fi/tyopaikat/haku/{query_slug}?sivu={page}"
