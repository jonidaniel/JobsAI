"""
JobsAI/src/jobsai/api/server.py

FastAPI server that exposes the full JobsAI pipeline as an HTTP endpoint.

Running:
    uvicorn server:app --reload
"""

import logging
from datetime import datetime
from typing import Dict, Any

from pydantic import BaseModel
from fastapi import FastAPI

from agents import (
    ProfilerAgent,
    SearcherAgent,
    ScorerAgent,
    ReporterAgent,
    GeneratorAgent,
)

from config.paths import (
    SKILL_PROFILES_PATH,
    JOB_LISTINGS_RAW_PATH,
    JOB_LISTINGS_SCORED_PATH,
    REPORTS_PATH,
    LETTERS_PATH,
)
from config.prompts import SYSTEM_PROMPT, USER_PROMPT
from config.settings import (
    JOB_BOARDS,
    DEEP_MODE,
    REPORT_SIZE,
    LETTER_STYLE,
    CONTACT_INFORMATION,
)

# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------- FastAPI Setup -------------

app = FastAPI(
    title="JobsAI Backend",
    description="API that triggers the full JobsAI job analysis pipeline.",
    version="1.0",
)


class FrontendPayload(BaseModel):
    """Accept arbitrary key-value pairs from the frontend."""
    __root__: Dict[str, Any]


# ------------- Pipeline Function -------------

def run_full_pipeline(frontend_answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Triggers the complete JobsAI pipeline using the existing agent architecture.
    Returns a summary dictionary of what was generated.
    """

    logging.info("Pipeline starting. Received answers:")
    logging.info(frontend_answers)

    # One timestamp per pipeline run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Initialize agents
    profiler = ProfilerAgent(SKILL_PROFILES_PATH, timestamp)
    searcher = SearcherAgent(JOB_BOARDS, DEEP_MODE, JOB_LISTINGS_RAW_PATH, timestamp)
    scorer = ScorerAgent(JOB_LISTINGS_RAW_PATH, JOB_LISTINGS_SCORED_PATH, timestamp)
    reporter = ReporterAgent(JOB_LISTINGS_SCORED_PATH, REPORTS_PATH, timestamp)
    generator = GeneratorAgent(LETTERS_PATH, timestamp)

    # ---- Step 1: profile ----
    # NOTE: You may want to merge frontend_answers into USER_PROMPT if needed.
    skill_profile = profiler.create_profile(SYSTEM_PROMPT, USER_PROMPT)

    # ---- Step 2: job search ----
    searcher.search_jobs(skill_profile.model_dump())

    # ---- Step 3: score jobs ----
    scorer.score_jobs(skill_profile)

    # ---- Step 4: report ----
    job_report = reporter.generate_report(skill_profile, REPORT_SIZE)

    # ---- Step 5: generate letters ----
    generator.generate_letters(
        skill_profile, job_report, LETTER_STYLE, CONTACT_INFORMATION
    )

    logging.info("Pipeline completed.")

    # Return minimal JSON info. You can include more if needed.
    return {
        "status": "completed",
        "timestamp": timestamp,
        "skill_profile_file": str(SKILL_PROFILES_PATH),
        "scored_jobs_file": str(JOB_LISTINGS_SCORED_PATH),
        "report_file": str(REPORTS_PATH),
        "letters_folder": str(LETTERS_PATH),
    }


# ------------- API Route -------------

@app.post("/api/endpoint")
async def trigger_pipeline(payload: FrontendPayload):
    """
    Endpoint called from the frontend.
    The request body is the JSON collected from sliders & text fields.
    """
    data = payload.__root__
    logging.info(f"Received API request with {len(data)} fields.")

    result = run_full_pipeline(data)
    return result


# ------------- Run Standalone -------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
