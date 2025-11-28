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
from typing import Dict

from docx import Document

from jobsai.agents import (
    ProfilerAgent,
    SearcherAgent,
    ScorerAgent,
    ReporterAgent,
    GeneratorAgent,
)

from jobsai.config.settings import (
    JOB_BOARDS,
    DEEP_MODE,
    REPORT_SIZE,
    LETTER_STYLE,
    CONTACT_INFORMATION,
)

logging.basicConfig(level=logging.INFO)
# For debug logging
# logging.basicConfig(level=logging.DEBUG)


def main(submits: Dict) -> Document:
    """Launch the agent pipeline.

    Returns:
        Document: The final cover letter.
    """

    # A constant timestamp for the whole workflow
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Initialize agents with constant values
    profiler = ProfilerAgent(timestamp)
    searcher = SearcherAgent(JOB_BOARDS, DEEP_MODE, timestamp)
    scorer = ScorerAgent(timestamp)
    reporter = ReporterAgent(timestamp)
    generator = GeneratorAgent(timestamp)

    # WILL BE ACCEPTED FROM FRONTEND FROM A TEXT FIELD LATER
    user_input = "My name is Joni Potala.\nI have developed software since 2020.\
        I have built and published multiple full-stack apps (frontend, backend, database, desktop, mobile).\
            I have built multi-agent orchestrations with OpenAI Agents SDK for half a year.\
                I have very good soft skills."

    # 1. Assess a candidate and return a skill profile of them
    skill_profile = profiler.create_profile(user_input, submits)

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
    document = generator.generate_letters(
        skill_profile, job_report, LETTER_STYLE, CONTACT_INFORMATION
    )

    return {
        "document": document,
        "timestamp": timestamp,
        "filename": f"{timestamp}_cover_letter.docx",
    }


# For running as standalone with 'uv run src/jobsai/main.py'
if __name__ == "__main__":
    main({})
