"""
JOBSAI
BACKEND ENTRY POINT

This module launches the backend of JobsAI.
It initializes all agents, loads configuration files, sets up logging, and handles workflow orchestration.

For overall project description, see README.md or docs/README.md.

Date: Fall 2025
Author: Joni Mäkinen
"""

import logging
from datetime import datetime

from jobsai.agents import (
    ProfilerAgent,
    SearcherAgent,
    ScorerAgent,
    ReporterAgent,
    GeneratorAgent,
)

from jobsai.config.prompts import SYSTEM_PROMPT
from jobsai.config.settings import (
    JOB_BOARDS,
    DEEP_MODE,
    REPORT_SIZE,
    LETTER_STYLE,
    CONTACT_INFORMATION,
)
from jobsai.config.paths import (
    SKILL_PROFILES_PATH,
    JOB_LISTINGS_RAW_PATH,
    JOB_LISTINGS_SCORED_PATH,
    REPORTS_PATH,
    LETTERS_PATH,
)

logging.basicConfig(level=logging.INFO)
# For debug logging
# logging.basicConfig(level=logging.DEBUG)


def main(submits):
    """
    Launch JobsAI.
    """

    # A constant timestamp for the whole workflow
    TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Initialize agents with constant values
    profiler = ProfilerAgent(SKILL_PROFILES_PATH, TIMESTAMP)
    searcher = SearcherAgent(JOB_BOARDS, DEEP_MODE, JOB_LISTINGS_RAW_PATH, TIMESTAMP)
    scorer = ScorerAgent(JOB_LISTINGS_RAW_PATH, JOB_LISTINGS_SCORED_PATH, TIMESTAMP)
    reporter = ReporterAgent(JOB_LISTINGS_SCORED_PATH, REPORTS_PATH, TIMESTAMP)
    generator = GeneratorAgent(LETTERS_PATH, TIMESTAMP)

    # 1. Assess a candidate and return a skill profile of them
    skill_profile = profiler.create_profile(SYSTEM_PROMPT, submits)

    # 2. Build search queries based on the skill profile
    # Then scrape job boards for job listings
    # Store the raw listings to /data/job_listings/raw/
    searcher.search_jobs(skill_profile.model_dump())

    # 3. Load the raw listings from /data/job_listings/raw/
    # Then score them based on relevancy to the candidate's skill profile
    # Save the scored listings to /data/job_listings/scored/scored_jobs.json
    scorer.score_jobs(skill_profile=skill_profile)

    # 4. Write a report/an analysis on the findings and save it to /data/reports/job_report.txt
    job_report = reporter.generate_report(skill_profile, REPORT_SIZE)

    # 5. Generate cover letters for each job
    generator.generate_letters(
        skill_profile, job_report, LETTER_STYLE, CONTACT_INFORMATION
    )

    return {"status": "completed"}


# For running as standalone with 'uv run src/jobsai/main.py'
if __name__ == "__main__":
    main()
