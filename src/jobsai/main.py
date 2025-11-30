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

from jobsai.agents import (
    ProfilerAgent,
    SearcherAgent,
    ScorerAgent,
    ReporterAgent,
    GeneratorAgent,
)

from jobsai.config.settings import (
    job_boards,
    deep_mode,
    report_size,
    letter_style,
    contact_information,
)

logging.basicConfig(level=logging.INFO)
# For debug logging
# logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)


def main(form_submissions: Dict) -> Dict:
    """
    Launch the complete JobsAI agent pipeline.

    This is the main orchestration function that runs all agents in sequence:
    1. ProfilerAgent: Creates/updates candidate skill profile from form submissions
    2. SearcherAgent: Scrapes job boards for relevant job listings
    3. ScorerAgent: Scores job listings based on skill profile match
    4. ReporterAgent: Generates analysis report on top-scoring jobs
    5. GeneratorAgent: Creates cover letter document based on report

    Args:
        form_submissions (Dict): Form data from frontend containing:
            - General questions (text fields)
            - Technology experience levels (slider values 0-7)
            - Multiple choice selections (e.g., experience levels)

    Returns:
        Dict: Dictionary containing:
            - "document" (Document): The generated cover letter as a Word document
            - "timestamp" (str): Timestamp used for file naming (format: YYYYMMDD_HHMMSS)
            - "filename" (str): Suggested filename for the cover letter document
    """

    # Generate a constant timestamp for the whole workflow
    # Used for consistent file naming across all agents
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    try:
        # Initialize all agents with the shared timestamp
        # Each agent uses the timestamp to create consistently named output files
        logger.info("Initializing agents...")
        profiler = ProfilerAgent(timestamp)
        searcher = SearcherAgent(job_boards, deep_mode, timestamp)
        scorer = ScorerAgent(timestamp)
        reporter = ReporterAgent(timestamp)
        generator = GeneratorAgent(timestamp)
    except Exception as e:
        error_msg = f"Failed to initialize agents: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    # Step 1: Assess candidate and create/update skill profile
    # Uses LLM to extract structured skill information from form submissions
    try:
        logger.info("Step 1/5: Creating skill profile...")
        skill_profile = profiler.create_profile(form_submissions)
        logger.info("Step 1/5: Skill profile created successfully")
    except Exception as e:
        error_msg = f"Step 1/5 (Profile Creation) failed: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    # Step 2: Build search queries from skill profile and scrape job boards
    # Queries are generated deterministically from profile keywords
    # Raw job listings are saved to /data/job_listings/raw/{timestamp}_{job_board}_{query}.json
    try:
        logger.info("Step 2/5: Searching job boards...")
        searcher.search_jobs(skill_profile.model_dump())
        logger.info("Step 2/5: Job search completed successfully")
    except Exception as e:
        error_msg = f"Step 2/5 (Job Search) failed: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    # Step 3: Score job listings based on relevancy to candidate's skill profile
    # Compares job descriptions with profile keywords to compute match scores
    # Scored listings are saved to /data/job_listings/scored/{timestamp}_scored_jobs.json
    try:
        logger.info("Step 3/5: Scoring job listings...")
        scorer.score_jobs(skill_profile=skill_profile)
        logger.info("Step 3/5: Job scoring completed successfully")
    except Exception as e:
        error_msg = f"Step 3/5 (Job Scoring) failed: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    # Step 4: Generate analysis report on top-scoring jobs
    # Uses LLM to create personalized cover letter instructions for each job (used by GeneratorAgent)
    # Report is saved to /data/reports/job_report.txt
    try:
        logger.info("Step 4/5: Generating job report...")
        job_report = reporter.generate_report(skill_profile, report_size)
        logger.info("Step 4/5: Job report generated successfully")
    except Exception as e:
        error_msg = f"Step 4/5 (Report Generation) failed: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    # Step 5: Generate cover letter document
    # Uses LLM to write cover letter based on skill profile and job report
    # Document is saved to /data/cover_letters/{timestamp}_cover_letter.docx and returned
    try:
        logger.info("Step 5/5: Generating cover letter...")
        document = generator.generate_letters(
            skill_profile, job_report, letter_style, contact_information
        )
        logger.info("Step 5/5: Cover letter generated successfully")
    except Exception as e:
        error_msg = f"Step 5/5 (Cover Letter Generation) failed: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    # Return document and metadata for API response
    logger.info("Pipeline completed successfully")
    return {
        "document": document,
        "timestamp": timestamp,
        "filename": f"{timestamp}_cover_letter.docx",
    }


# For running as standalone with 'uv run src/jobsai/main.py'
if __name__ == "__main__":
    main({})
