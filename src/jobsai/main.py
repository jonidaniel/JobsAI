"""
JobsAI Backend Pipeline Orchestration.

This module serves as the main entry point for the JobsAI backend pipeline.
It orchestrates the complete workflow from form submissions to cover letter generation:

1. ProfilerAgent: Creates candidate profile from form submissions
2. QueryBuilderAgent: Generates search keywords from profile
3. SearcherService: Searches job boards for relevant positions
4. ScorerService: Scores jobs based on candidate profile match
5. AnalyzerAgent: Analyzes top-scoring jobs and generates cover letter instructions
6. GeneratorAgent: Generates personalized cover letter document

The pipeline uses a decorator-based approach for consistent error handling and logging
across all steps.

For overall project description, see README.md or docs/README.md.
"""

import logging
from datetime import datetime
from typing import Dict, Callable, Any, Optional
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
from jobsai.utils.exceptions import CancellationError

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


def main(
    form_submissions: Dict,
    progress_callback: Optional[Callable[[str, str], None]] = None,
    cancellation_check: Optional[Callable[[], bool]] = None,
) -> Dict:
    """
    Launch the complete JobsAI agent pipeline.

    This is the main orchestration function that runs all agents in sequence:
    1. ProfilerAgent: Creates/updates candidate profile from form submissions
    2. QueryBuilderAgent: Generates search keywords from profile
    3. SearcherService: Searches job boards for relevant positions
    4. ScorerService: Scores jobs based on candidate profile match
    5. AnalyzerAgent: Writes an analysis on top-scoring jobs
    6. GeneratorAgent: Creates cover letter document based on the analysis

    Args:
        form_submissions (Dict): Form data from frontend containing:
            - General questions (text fields)
            - Technology experience levels (slider values 0-7)
            - Multiple choice selections (e.g., experience levels)
        progress_callback (Optional[Callable[[str, str], None]]): Optional callback
            function that receives (phase, message) for progress updates.
            Phase values: "profiling", "searching", "scoring", "analyzing", "generating"
        cancellation_check (Optional[Callable[[], bool]]): Optional callable that
            returns True if the pipeline should be cancelled. Checked at key points
            during execution.

    Returns:
        Dict: Dictionary containing:
            - "document" (Document): The generated cover letter as a Word document
            - "timestamp" (str): Timestamp used for file naming (format: YYYYMMDD_HHMMSS)
            - "filename" (str): Suggested filename for the cover letter document

    Raises:
        CancellationError: If cancellation_check returns True during execution
    """
    print("[MAIN] main() function called")
    logger.info("[MAIN] main() function called, starting pipeline")

    # Extract and transform form submission data
    print("[MAIN] About to extract form data")
    logger.info("[MAIN] About to extract form data")
    answers = extract_form_data(form_submissions)
    print("[MAIN] Form data extracted")
    logger.info("[MAIN] Form data extracted")
    job_boards = answers["job_boards"]
    deep_mode = answers["deep_mode"]
    cover_letter_num = answers["cover_letter_num"]
    cover_letter_style = answers["cover_letter_style"]
    tech_stack = answers["tech_stack"]
    logger.info(f"JOB BOARDS: {job_boards}")
    logger.info(f"DEEP MODE: {deep_mode}")
    logger.info(f"COVER LETTER NUM: {cover_letter_num}")
    logger.info(f"COVER LETTER STYLE: {cover_letter_style}")
    logger.info(f"TECH STACK: {tech_stack}")

    # Generate a timestamp for consistent file naming
    # Used throughout the pipeline to insert the same datetime to all output files
    # (candidate profiles, raw job listings, scored job listings, job analyses, and cover letters)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Initialize all agents and services
    try:
        logger.info(" Initializing agents and services...")
        # 1. Profiles the candidate
        profiler = ProfilerAgent()
        # 2. Creates keywords from the candidate profile
        query_builder = QueryBuilderAgent()
        # 3. Searches job boards for relevant jobs
        searcher = SearcherService(timestamp)
        # 4. Scores the jobs
        scorer = ScorerService(timestamp)
        # 5. Writes an analysis on the top-scoring jobs
        analyzer = AnalyzerAgent(timestamp)
        # 6. Generates cover letters based on the analysis
        generator = GeneratorAgent(timestamp)
        logger.info(" Agents and services initialized successfully")
    except Exception as e:
        error_msg = f" Failed to initialize agents and services: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    # Check for cancellation before starting
    if cancellation_check and cancellation_check():
        raise CancellationError("Pipeline cancelled before start")

    # Step 1: Profile the candidate
    # Uses LLM to extract the candidate's skills and experience from the form submissions
    # Returns a string of the candidate profile (e.g. "John Doe is a software engineer with 5 years of experience in Python and Java.")
    logger.info("About to call progress_callback for profiling phase")
    print("[MAIN] About to call progress_callback for profiling phase")
    if progress_callback:
        print(
            "[MAIN] Calling progress_callback('profiling', 'Creating your profile...')"
        )
        progress_callback("profiling", "Creating your profile...")
        print("[MAIN] progress_callback completed")
    else:
        print("[MAIN] progress_callback is None!")

    logger.info("About to start profiling step")
    print("[MAIN] About to start profiling step")

    @pipeline_step("Profiling candidate", 1, 6)
    def _step1_profile():
        if cancellation_check and cancellation_check():
            raise CancellationError("Pipeline cancelled during profiling")
        logger.info("Calling profiler.create_profile()")
        print("[MAIN] Calling profiler.create_profile()")
        result = profiler.create_profile(form_submissions)
        logger.info("profiler.create_profile() completed")
        print(
            f"[MAIN] profiler.create_profile() completed, result length: {len(result) if result else 0}"
        )
        return result

    profile = _step1_profile()
    logger.info(f"Profile created, length: {len(profile) if profile else 0}")
    print(f"[MAIN] Profile created, length: {len(profile) if profile else 0}")

    # Step 2: Create search keywords
    # Uses LLM to create search keywords from the candidate profile
    # Returns a list of search keywords (e.g. ["ai engineer", "software engineer", "data scientist"])
    if cancellation_check and cancellation_check():
        raise CancellationError("Pipeline cancelled before keyword creation")

    @pipeline_step("Creating keywords", 2, 6)
    def _step2_keywords():
        if cancellation_check and cancellation_check():
            raise CancellationError("Pipeline cancelled during keyword creation")
        return query_builder.create_keywords(profile)

    keywords = _step2_keywords()

    # Step 3: Search job boards
    # Searches job boards for relevant jobs using the search keywords
    # Returns a list of raw job listings
    # (e.g. [{"title": "Software Engineer", "company": "Google", "location": "San Francisco", "url": "https://www.google.com", "description_snippet": "We are looking for a software engineer with 5 years of experience in Python and Java."}])
    # The raw jobs are also saved to /src/jobsai/data/job_listings/raw/{timestamp}_{job_board}_{query}.json for convenience
    if progress_callback:
        progress_callback("searching", "Searching for jobs...")

    if cancellation_check and cancellation_check():
        raise CancellationError("Pipeline cancelled before job search")

    @pipeline_step("Searching jobs", 3, 6)
    def _step3_search():
        if cancellation_check and cancellation_check():
            raise CancellationError("Pipeline cancelled during job search")
        # Pass cancellation_check to searcher for checking during long operations
        return searcher.search_jobs(keywords, job_boards, deep_mode, cancellation_check)

    raw_jobs = _step3_search()

    # Step 4: Score job listings
    # Scores the job listings based on the candidate's technology stack
    # Returns a list of scored job listings
    # (e.g. [{"title": "Software Engineer", "company": "Google", "location": "San Francisco", "url": "https://www.google.com", "description_snippet": "We are looking for a software engineer with 5 years of experience in Python and Java.", "score": 80}])
    # The scored jobs are also saved to /src/jobsai/data/job_listings/scored/{timestamp}_scored_jobs.json for convenience
    if progress_callback:
        progress_callback("scoring", "Scoring the jobs...")

    if cancellation_check and cancellation_check():
        raise CancellationError("Pipeline cancelled before scoring")

    @pipeline_step("Scoring jobs", 4, 6)
    def _step4_score():
        if cancellation_check and cancellation_check():
            raise CancellationError("Pipeline cancelled during scoring")
        # Pass cancellation_check to scorer for checking during job processing loop
        scored = scorer.score_jobs(raw_jobs, tech_stack, cancellation_check)
        if not scored:
            raise ValueError(
                "No jobs were scored. This may indicate an issue with job search or scoring logic."
            )
        return scored

    scored_jobs = _step4_score()

    # Step 5: Write an analysis on top-scoring jobs
    # Uses LLM to create personalized cover letter instructions for each job
    # Returns a string of the job analysis
    # (e.g. "The top-scoring job is for a software engineer at Google in San Francisco. The job analysis is: We are looking for a software engineer with 5 years of experience in Python and Java.")
    # The job analysis is also saved to /src/jobsai/data/job_analyses/{timestamp}_job_analysis.txt for convenience
    if progress_callback:
        progress_callback("analyzing", "Doing analysis...")

    if cancellation_check and cancellation_check():
        raise CancellationError("Pipeline cancelled before analysis")

    @pipeline_step("Analyzing jobs", 5, 6)
    def _step5_analyze():
        if cancellation_check and cancellation_check():
            raise CancellationError("Pipeline cancelled during analysis")
        # Pass cancellation_check to analyzer for checking during LLM calls in loop
        return analyzer.write_analysis(
            scored_jobs, profile, cover_letter_num, cancellation_check
        )

    job_analysis = _step5_analyze()

    # Step 6: Generate cover letter document
    # Uses LLM to write cover letter based on the candidate profile, the job analysis and the cover letter style
    # Returns a Document object
    # The document is also saved to /src/jobsai/data/cover_letters/{timestamp}_cover_letter.docx for convenience
    if progress_callback:
        progress_callback("generating", "Generating cover letters for you...")

    if cancellation_check and cancellation_check():
        raise CancellationError("Pipeline cancelled before generation")

    @pipeline_step("Generating cover letters", 6, 6)
    def _step6_generate():
        if cancellation_check and cancellation_check():
            raise CancellationError("Pipeline cancelled during generation")
        return generator.generate_letters(job_analysis, profile, cover_letter_style)

    cover_letters = _step6_generate()

    # Return document and metadata for API response
    logger.info(" Pipeline completed successfully")
    return {
        "document": cover_letters,
        "timestamp": timestamp,
        "filename": f"{timestamp}_cover_letter.docx",
    }


# For running as standalone
if __name__ == "__main__":
    main({})
