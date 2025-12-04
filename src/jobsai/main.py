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
    QueryBuilderAgent,
    SearcherService,
    ScorerService,
    AnalyzerAgent,
    GeneratorAgent,
)

from jobsai.utils.form_data import extract_form_data

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def main(form_submissions: Dict) -> Dict:
    """
    Launch the complete JobsAI agent pipeline.

    This is the main orchestration function that runs all agents in sequence:
    1. ProfilerAgent: Creates/updates candidate profile from form submissions
    2. SearcherAgent: Scrapes job boards for relevant job listings
    3. ScorerAgent: Scores job listings based on skill profile match
    4. AnalyzerAgent: Writes an analysis on top-scoring jobs
    5. GeneratorAgent: Creates cover letter document based on the analysis

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

    # Extract and transform form submission data
    answers = extract_form_data(form_submissions)
    job_boards = answers["job_boards"]
    deep_mode = answers["deep_mode"]
    cover_letter_num = answers["cover_letter_num"]
    cover_letter_style = answers["cover_letter_style"]

    # Extract technology categories directly from form_submissions
    # These are optional fields, so use .get() with empty list as default
    languages = form_submissions.get("languages", [])
    databases = form_submissions.get("databases", [])
    cloud_development = form_submissions.get("cloud-development", [])
    web_frameworks = form_submissions.get("web-frameworks", [])
    dev_ides = form_submissions.get("dev-ides", [])
    llms = form_submissions.get("llms", [])
    doc_and_collab = form_submissions.get("doc-and-collab", [])
    operating_systems = form_submissions.get("operating-systems", [])

    tech_stack = [
        languages,
        databases,
        cloud_development,
        web_frameworks,
        dev_ides,
        llms,
        doc_and_collab,
        operating_systems,
    ]

    # Generate a timestamp for consistent file naming
    # Used throughout the pipeline to insert the same datetime to all output files
    # (candidate profiles, raw job listings, scored job listings, job analyses, and cover letters)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    try:
        # Initialize all agents and services
        logger.info("Initializing agents and services...")
        profiler = ProfilerAgent()
        query_builder = QueryBuilderAgent()
        searcher = SearcherService(timestamp)
        scorer = ScorerService(timestamp)
        analyzer = AnalyzerAgent(timestamp)
        generator = GeneratorAgent(timestamp)
    except Exception as e:
        error_msg = f"Failed to initialize agents and services: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    # Step 1: Assess candidate and create/update profile
    # Uses LLM to extract structured skill information from form submissions
    try:
        logger.info(" Step 1/6: Creating candidate profile...")
        profile = profiler.create_profile(form_submissions)
        logger.info(" Step 1/6: Candidate profile created successfully")
    except Exception as e:
        error_msg = f" Step 1/6 Candidate profile creation failed: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    # Step 2: Create keywords
    # Uses LLM to create keywords from candidate profile
    try:
        logger.info(" Step 2/6: Creating keywords...")
        keywords = query_builder.create_keywords(profile)
        logger.info(" Step 2/6: Keywords created successfully")
    except Exception as e:
        error_msg = f" Step 2/6 Keywords creation failed: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    # Step 3: Search job boards
    # Queries are generated deterministically from candidate profile keywords
    # Returns a list of raw job listings
    # The raw jobs are also saved to /src/jobsai/data/job_listings/raw/{timestamp}_{job_board}_{query}.json for later use
    try:
        logger.info(" Step 3/6: Searching job boards...")
        raw_jobs = searcher.search_jobs(
            keywords,
            job_boards,
            deep_mode,
        )
        logger.info(" Step 3/6: Job search completed successfully")
    except Exception as e:
        error_msg = f" Step 3/6 Job search failed: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    # Step 4: Score job listings
    # Compares job descriptions with profile keywords to compute match scores
    # Returns a list of scored job listings
    # The scored jobs are also saved to /src/jobsai/data/job_listings/scored/{timestamp}_scored_jobs.json for later use
    try:
        print()
        logger.info(" Step 4/6: Scoring job listings...")
        scored_jobs = scorer.score_jobs(raw_jobs, tech_stack)
        logger.info(" Step 4/6: Job scoring completed successfully")
    except Exception as e:
        error_msg = f" Step 4/6 Job scoring failed: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    # Step 5: Write an analysis on top-scoring jobs
    # Uses LLM to create personalized cover letter instructions for each job (used by GeneratorAgent)
    # Returns a string of the job analysis
    # The report is also saved to /src/jobsai/data/job_analyses/{timestamp}_job_analysis.txt for later use
    try:
        logger.info(" Step 5/6: Analyzing jobs...")
        job_analysis = analyzer.write_analysis(
            scored_jobs,
            profile,
            cover_letter_num,
        )
        logger.info(" Step 5/6: Job analysis completed successfully")
    except Exception as e:
        error_msg = f" Step 5/6 Job analysis failed: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    # Step 6: Generate cover letter document
    # Uses LLM to write cover letter based on profile, job analysis and cover letter style
    # Returns a Document object
    # The document is also saved to /src/jobsai/data/cover_letters/{timestamp}_cover_letter.docx for later use
    try:
        logger.info(" Step 6/6: Generating cover letters...")
        cover_letters = generator.generate_letters(
            job_analysis, profile, cover_letter_style
        )
        logger.info(" Step 6/6: Cover letters generated successfully")
    except Exception as e:
        error_msg = f" Step 6/6 Cover letter generation failed: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    # Return document and metadata for API response
    logger.info(" Pipeline completed successfully")
    return {
        "document": cover_letters,
        "timestamp": timestamp,
        "filename": f"{timestamp}_cover_letter.docx",
    }


# For running as standalone with 'uv run src/jobsai/main.py'
if __name__ == "__main__":
    main({})
