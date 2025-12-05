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
from typing import Dict, Callable, Any
from functools import wraps

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


def pipeline_step(step_name: str, step_number: int, total_steps: int):
    """
    Decorator for pipeline steps that provides consistent error handling and logging.

    Args:
        step_name: Human-readable name of the step
        step_number: Step number (1-indexed)
        total_steps: Total number of steps in pipeline
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                logger.info(f" Step {step_number}/{total_steps}: {step_name}...")
                result = func(*args, **kwargs)
                logger.info(
                    f" Step {step_number}/{total_steps}: {step_name} completed successfully"
                )
                return result
            except Exception as e:
                error_msg = (
                    f" Step {step_number}/{total_steps}: {step_name} failed: {str(e)}"
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e

        return wrapper

    return decorator


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
    tech_stack = answers["tech_stack"]
    job_boards = answers["job_boards"]
    deep_mode = answers["deep_mode"]
    cover_letter_num = answers["cover_letter_num"]
    cover_letter_style = answers["cover_letter_style"]

    # Generate a timestamp for consistent file naming
    # Used throughout the pipeline to insert the same datetime to all output files
    # (candidate profiles, raw job listings, scored job listings, job analyses, and cover letters)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Initialize all agents and services
    try:
        logger.info("Initializing agents and services...")
        profiler = ProfilerAgent()  # 1. Profiles the candidate
        query_builder = (
            QueryBuilderAgent()
        )  # 2. Creates keywords from the candidate profile
        searcher = SearcherService(
            timestamp
        )  # 3. Searches job boards for relevant jobs
        scorer = ScorerService(timestamp)  # 4. Scores the jobs
        analyzer = AnalyzerAgent(
            timestamp
        )  # 5. Writes an analysis on the top-scoring jobs
        generator = GeneratorAgent(
            timestamp
        )  # 6. Generates cover letters based on the analysis
        logger.info("Agents and services initialized successfully")
    except Exception as e:
        error_msg = f"Failed to initialize agents and services: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    # Step 1: Assess candidate and create/update profile
    # Uses LLM to extract structured skill information from form submissions
    @pipeline_step("Profiling candidate", 1, 6)
    def _step1_profile():
        return profiler.create_profile(form_submissions)

    profile = _step1_profile()

    # Step 2: Create keywords
    # Uses LLM to create keywords from candidate profile
    @pipeline_step("Creating keywords", 2, 6)
    def _step2_keywords():
        return query_builder.create_keywords(profile)

    keywords = _step2_keywords()

    # Step 3: Search job boards
    # Queries are generated deterministically from candidate profile keywords
    # Returns a list of raw job listings
    # The raw jobs are also saved to /src/jobsai/data/job_listings/raw/{timestamp}_{job_board}_{query}.json for later use
    @pipeline_step("Searching jobs", 3, 6)
    def _step3_search():
        return searcher.search_jobs(keywords, job_boards, deep_mode)

    raw_jobs = _step3_search()

    # Step 4: Score job listings
    # Compares job descriptions with profile keywords to compute match scores
    # Returns a list of scored job listings
    # The scored jobs are also saved to /src/jobsai/data/job_listings/scored/{timestamp}_scored_jobs.json for later use
    @pipeline_step("Scoring jobs", 4, 6)
    def _step4_score():
        scored = scorer.score_jobs(raw_jobs, tech_stack)
        if not scored:
            raise ValueError(
                "No jobs were scored. This may indicate an issue with job search or scoring logic."
            )
        return scored

    scored_jobs = _step4_score()

    # Step 5: Write an analysis on top-scoring jobs
    # Uses LLM to create personalized cover letter instructions for each job (used by GeneratorAgent)
    # Returns a string of the job analysis
    # The report is also saved to /src/jobsai/data/job_analyses/{timestamp}_job_analysis.txt for later use
    @pipeline_step("Analyzing jobs", 5, 6)
    def _step5_analyze():
        return analyzer.write_analysis(scored_jobs, profile, cover_letter_num)

    job_analysis = _step5_analyze()

    # Step 6: Generate cover letter document
    # Uses LLM to write cover letter based on profile, job analysis and cover letter style
    # Returns a Document object
    # The document is also saved to /src/jobsai/data/cover_letters/{timestamp}_cover_letter.docx for later use
    @pipeline_step("Generating cover letters", 6, 6)
    def _step6_generate():
        return generator.generate_letters(job_analysis, profile, cover_letter_style)

    cover_letters = _step6_generate()

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
