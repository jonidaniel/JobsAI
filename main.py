# ---------- JOBSAI ----------

# Version: 0.1.0
# Date: Fall 2025
# Author: Joni Mäkinen

# An agentic AI system for end-to-end automated job searching and job application document generation:
# enter your skills and preferences to the system once and get job recommendations and cover letters delivered to you continuously.
# Checks input resources consistently and updates search queries autonomously.

import logging
from datetime import datetime

from agents import (
    ProfilerAgent,
    SearcherAgent,
    ScorerAgent,
    ReporterAgent,
    GeneratorAgent,
)

from config.prompts import SYSTEM_PROMPT, USER_PROMPT
from config.settings import JOB_BOARDS, DEEP_MODE, LETTER_STYLE
from config.paths import (
    SKILL_PROFILES_PATH,
    JOB_LISTINGS_RAW_PATH,
    JOB_LISTINGS_SCORED_PATH,
    REPORTS_PATH,
    LETTERS_PATH,
)

logging.basicConfig(level=logging.INFO)
# For debug logging
# logging.basicConfig(level=logging.DEBUG)


def main():
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
    skill_profile = profiler.create_profile(SYSTEM_PROMPT, USER_PROMPT)

    # 2. Build search queries based on the skill profile
    # Then scrape job boards for job listings
    # Store the raw listings to /data/job_listings/raw/
    searcher.search_jobs(skill_profile.model_dump())

    # 3. Load the raw listings from /data/job_listings/raw/
    # Then score them based on relevancy to the candidate's skill profile
    # Save the scored listings to /data/job_listings/scored/scored_jobs.json
    scorer.score_jobs(skill_profile=skill_profile)

    # 4. Write a report/an analysis on the findings and save it to /data/reports/job_report.txt
    job_report = reporter.generate_report(top_n=10)

    # 5. Generate cover letters for each job
    generator.generate_letters(skill_profile, job_report, LETTER_STYLE)


if __name__ == "__main__":
    main()
