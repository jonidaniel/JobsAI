# ---------- JOBSAI ----------

# Version: 0.1.0
# Date: Fall 2025
# Author: Joni Mäkinen

# An agentic AI system for end-to-end automated job searching and job application document generation:
# enter your skills and preferences to the system once and get job recommendations and cover letters delivered to you continuously.
# Checks input resources consistently and updates search queries autonomously.

import logging

from agents import (
    ProfilerAgent,
    SearcherAgent,
    ScorerAgent,
    ReporterAgent,
    GeneratorAgent,
)

from config.prompts import SYSTEM_PROMPT, USER_PROMPT
from config.settings import JOB_BOARDS, DEEP_MODE
from config.paths import (
    SKILL_PROFILE_PATH,
    JOB_LISTINGS_RAW_PATH,
    JOB_LISTINGS_SCORED_PATH,
    REPORTS_PATH,
)

logging.basicConfig(level=logging.INFO)
# For debug logging
# logging.basicConfig(level=logging.DEBUG)


def main():
    """
    Launch JobsAI.
    """

    # Initialize agents with constant values
    profiler = ProfilerAgent(SKILL_PROFILE_PATH)
    searcher = SearcherAgent(JOB_BOARDS, DEEP_MODE, JOB_LISTINGS_RAW_PATH)
    scorer = ScorerAgent(JOB_LISTINGS_RAW_PATH, JOB_LISTINGS_SCORED_PATH)
    reporter = ReporterAgent(JOB_LISTINGS_SCORED_PATH, REPORTS_PATH)
    generator = GeneratorAgent()

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
    report_text = reporter.generate_report(top_n=10)

    # 5. Generate documents for each job
    documents = generator.generate_application(skill_profile, report_text)
    print(documents)


if __name__ == "__main__":
    main()
