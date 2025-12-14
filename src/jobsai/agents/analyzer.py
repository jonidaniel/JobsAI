"""
Analyzer Agent - Job Analysis and Cover Letter Instruction Generation.

This module contains the AnalyzerAgent class, which analyzes top-scoring job
listings and generates personalized cover letter instructions for each position.
The agent uses an LLM to analyze job descriptions against candidate profiles
and create specific instructions for writing tailored cover letters.

The analysis includes:
- Job details (title, company, location, score)
- Matched and missing skills
- Personalized cover letter writing instructions
"""

import os
from typing import List, Dict, Optional, Callable, Any

from jobsai.config.paths import JOB_ANALYSIS_PATH
from jobsai.config.prompts import (
    ANALYZER_SYSTEM_PROMPT as SYSTEM_PROMPT,
    ANALYZER_USER_PROMPT as USER_PROMPT,
)

from jobsai.utils.llms import call_llm
from jobsai.utils.exceptions import CancellationError
from jobsai.utils.logger import get_logger

logger = get_logger(__name__)


class AnalyzerAgent:
    """Agent responsible for analyzing top-scoring jobs and generating cover letter instructions.

    Processes the highest-scoring job listings and uses an LLM to generate
    personalized instructions for writing cover letters tailored to each position.
    The instructions focus on matching the candidate's skills to job requirements
    and highlighting relevant experience.

    The analysis is saved to disk for debugging and returned as formatted text
    that will be used by the GeneratorAgent to write the actual cover letters.

    Args:
        timestamp (str): Backend-wide timestamp for consistent file naming.
            Format: YYYYMMDD_HHMMSS (e.g., "20250115_143022")
    """

    def __init__(self, timestamp: str) -> None:
        self.timestamp: str = timestamp

    # ------------------------------
    # Public interface
    # ------------------------------
    def write_analysis(
        self,
        jobs: List[Dict[str, Any]],
        profile: str,
        analysis_size: int,
        cancellation_check: Optional[Callable[[], bool]] = None,
    ) -> str:
        """
        Write an analysis on the most-scored jobs.

        For each top-scoring job, the function:
        1. Uses an LLM to generate personalized cover letter instructions
        2. Formats the job details (title, company, location, score, etc.)
        3. Combines everything into a readable report

        The analysis is saved to /data/job_analyses/ and returned.

        Args:
            jobs (List[Dict]): The job listings.
            profile (str): The candidate profile text.
            analysis_size (int): The desired number of top jobs to include in the analysis.
            cancellation_check (Optional[Callable[[], bool]]): Optional callable
                that returns True if the operation should be cancelled. Checked
                before processing each job.

        Returns:
            str: The complete job analysis as a formatted text string.

        Raises:
            CancellationError: If cancellation_check returns True during execution
        """

        # Validate input
        if not jobs:
            logger.warning(" No scored jobs found for analysis.")
            raise ValueError("No scored jobs found for analysis.")

        # Initialize analysis report with header
        analysis_lines = ["Job Analysis", "=" * 40, f"Top {analysis_size} Jobs:\n"]

        # Process each top-scoring job (already sorted by score descending)
        for job in jobs[:analysis_size]:
            # Check for cancellation before processing each job
            if cancellation_check and cancellation_check():
                logger.info(" Job analysis cancelled by user")
                raise CancellationError("Pipeline cancelled during analysis")

            # Get full job description if available (from deep mode)
            # Falls back to description_snippet if full_description not available
            full_description = job.get("full_description") or job.get(
                "description_snippet", ""
            )

            # Generate personalized cover letter instructions using LLM
            # The LLM analyzes the job description against the candidate profile
            # and creates specific instructions for writing a tailored cover letter
            # that highlights relevant skills and experience
            # Note: LLM call itself cannot be interrupted, but we check before each call
            instructions = call_llm(
                SYSTEM_PROMPT,
                USER_PROMPT.format(
                    full_description=full_description,
                    profile=profile,
                ),
            )

            # Check for cancellation after LLM call (before processing result)
            if cancellation_check and cancellation_check():
                logger.info(" Job analysis cancelled by user")
                raise CancellationError("Pipeline cancelled during analysis")

            # Extract job metadata for the analysis report
            title = job.get("title") or "N/A"
            company = job.get("company") or "N/A"
            location = job.get("location") or "N/A"
            score = job.get("score", 0)
            matched = ", ".join(job.get("matched_skills", [])) or "None"
            missing = ", ".join(job.get("missing_skills", [])) or "None"
            url = job.get("url") or "N/A"

            # Format job details and LLM-generated instructions into report
            analysis_lines.append(f"Title: {title}")
            analysis_lines.append(f"Company: {company}")
            analysis_lines.append(f"Location: {location}")
            analysis_lines.append(f"Score: {score}%")
            analysis_lines.append(f"Matched Skills: {matched}")
            analysis_lines.append(f"Missing Skills: {missing}")
            analysis_lines.append(f"URL: {url}")
            analysis_lines.append(f"Instructions: {instructions}")
            analysis_lines.append("-" * 40)

        # Combine all analysis lines into a single text string
        analysis_text = "\n".join(analysis_lines)

        # Save analysis to disk for debugging and record-keeping
        filename = f"{self.timestamp}_job_analysis.txt"
        path = os.path.join(JOB_ANALYSIS_PATH, filename)

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(analysis_text)
            logger.info(
                "Saved job analysis",
                extra={"extra_fields": {"path": path, "timestamp": self.timestamp}},
            )
        except Exception as e:
            # Log error but don't fail - analysis text is still returned
            logger.error(
                "Failed to save job analysis to disk",
                extra={
                    "extra_fields": {
                        "path": path,
                        "timestamp": self.timestamp,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                },
            )

        return analysis_text
