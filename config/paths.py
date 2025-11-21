# ---------- PATHS ----------

from pathlib import Path

SKILL_PROFILE_PATH = Path("memory/vector_db/skill_profile.json")
SKILL_PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)

JOB_LISTINGS_RAW_PATH = "data/job_listings/raw/"
JOB_LISTINGS_SCORED_PATH = "data/job_listings/scored/"

REPORTS_PATH = "data/reports/"

# ---------- URLS ----------

HOST_URL = "https://duunitori.fi"
SEARCH_URL_BASE = "https://duunitori.fi/tyopaikat/haku/{query_slug}?sivu={page}"
