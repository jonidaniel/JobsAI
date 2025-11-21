# ---------- JOBSAI ----------

# Version: 0.1.0
# Date: Fall 2025
# Author: Joni Mäkinen

# An agentic AI system for end-to-end automated job searching and job application document generation:
# enter your skills and preferences to the system once and get job recommendations and cover letters delivered to you continuously.
# Checks input resources consistently and updates search queries autonomously.

import os
import logging

from dotenv import load_dotenv

from agents import AssessorAgent, SearcherAgent, ScorerAgent, ReporterAgent

from config.prompts import PROMPT, SYSTEM_PROMPT
from config.settings import JOB_BOARDS, DEEP_MODE
from config.paths import SKILL_PROFILE_PATH, JOB_LISTINGS_RAW_PATH, JOB_LISTINGS_SCORED_PATH, REPORTS_PATH

logging.basicConfig(level=logging.INFO)
# For debug logging
#logging.basicConfig(level=logging.DEBUG)

load_dotenv()
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def main():
    assessor = AssessorAgent(OPENAI_MODEL, OPENAI_API_KEY, SKILL_PROFILE_PATH)
    searcher = SearcherAgent(JOB_BOARDS, DEEP_MODE)
    scorer = ScorerAgent(JOB_LISTINGS_RAW_PATH, JOB_LISTINGS_SCORED_PATH)
    reporter = ReporterAgent(JOB_LISTINGS_SCORED_PATH, REPORTS_PATH)

    # 1. Assess candidate
    # Returns a SkillProfile object
    skill_profile = assessor.assess(PROMPT, SYSTEM_PROMPT)

    # 2. Search jobs based on assessment
    # Uses skill_profile to form keyword searches
    # The keyword searches are then used to scrape popular job listing websites
    # Stores acquired job listings as JSON to /data/job_listings/raw/*.json
    searcher.search_jobs(skill_profile.model_dump())

    # 3. Score the jobs
    # Loads raw job listings JSON from /data/job_listings/raw/*.json
    # Saves scored job listings as JSON to /data/job_listings/scored/*.json
    scorer.score_jobs(skill_profile=skill_profile)

    # 4. Write a job listing report
    # Saves the report to /data/reports/job_report.txt
    reporter.generate_report(top_n=10)

if __name__ == "__main__":
    main()
