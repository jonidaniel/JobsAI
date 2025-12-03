"""
Orchestrates the writing of an analysis on the best-scored jobs.

CLASSES:
    AnalyzerAgent

FUNCTIONS (in order of workflow):
    1. write_analysis      (public use)
"""

import os
import logging
from typing import List, Dict

from jobsai.config.paths import JOB_ANALYSIS_PATH
from jobsai.config.prompts import (
    ANALYZER_SYSTEM_PROMPT as SYSTEM_PROMPT,
    ANALYZER_USER_PROMPT as USER_PROMPT,
)
from jobsai.config.schemas import SkillProfile

from jobsai.utils.llms import call_llm

logger = logging.getLogger(__name__)


class AnalyzerAgent:
    """Orchestrates the writing of an analysis on the best-scored jobs.

    Responsibilities:
    1. Sort the scored job listings by score descending
    2. Write an analysis of the top-scoring jobs

    Args:
        timestamp (str): The backend-wide timestamp of the moment when the main function was started.
    """

    def __init__(self, timestamp: str):
        self.timestamp = timestamp

    # ------------------------------
    # Public interface
    # ------------------------------
    def write_analysis(
        self, jobs: List[Dict], profile: SkillProfile, analysis_size: int
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
            profile (SkillProfile): The candidate profile.
            analysis_size (int): The desired number of top jobs to include in the analysis.

        Returns:
            str: The complete job analysis as a formatted text string.
        """

        # THIS IS NOT NEEDED SINCE WE ARE PASSING THE SCORED JOBS DIRECTLY
        # scored_jobs = self._load_scored_jobs()

        if not jobs:
            logger.warning(" No scored jobs found for reporting.")
            return ""

        # Sort jobs by score descending (already done in scorer, but safe to re-sort)
        jobs.sort(key=lambda x: x.get("score", 0), reverse=True)

        # Initialize report with header
        analysis_lines = ["Job Analysis", "=" * 40, f"Top {analysis_size} Jobs:\n"]

        # Process each top-scoring job
        for job in jobs[:analysis_size]:
            full_description = job.get("full_description")

            # Generate personalized cover letter instructions using LLM
            # The LLM analyzes the job description and skill profile to create
            # specific instructions for writing a tailored cover letter
            instructions = call_llm(
                SYSTEM_PROMPT,
                USER_PROMPT.format(
                    full_description=full_description,
                    skill_profile=profile,
                ),
            )

            # Get the job details
            title = job.get("title") or "N/A"
            company = job.get("company") or "N/A"
            location = job.get("location") or "N/A"
            score = job.get("score", 0)
            matched = ", ".join(job.get("matched_skills", []))
            missing = ", ".join(job.get("missing_skills", []))
            url = job.get("url") or "N/A"

            # Add the job details to the report
            analysis_lines.append(f"Title: {title}")
            analysis_lines.append(f"Company: {company}")
            analysis_lines.append(f"Location: {location}")
            analysis_lines.append(f"Score: {score}%")
            analysis_lines.append(f"Matched Skills: {matched}")
            analysis_lines.append(f"Missing Skills: {missing}")
            analysis_lines.append(f"URL: {url}")
            analysis_lines.append(f"Instructions: {instructions}")
            analysis_lines.append("-" * 40)

        analysis_text = "\n".join(analysis_lines)

        # Form a dated filename and make a path
        filename = f"{self.timestamp}_job_analysis.txt"
        path = os.path.join(JOB_ANALYSIS_PATH, filename)

        # Save to the path
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(analysis_text)

            logger.info(f" Saved job analysis to /{path}")
        except Exception as e:
            logger.error(f" Failed to save job analysis: {e}")

        return analysis_text

    # ------------------------------
    # Internal function
    # ------------------------------
    # def _load_scored_jobs(self) -> List[Dict]:
    #     """Load the scored job listings.

    #     Loads the scored job listings from SCORED_JOB_LISTING_PATH.

    #     Returns:
    #         List[Dict]: The list of scored job listings.
    #     """

    #     path = os.path.join(
    #         SCORED_JOB_LISTING_PATH, f"{self.timestamp}_scored_jobs.json"
    #     )
    #     if not os.path.exists(path):
    #         return []

    #     try:
    #         with open(path, "r", encoding="utf-8") as f:
    #             data = json.load(f)
    #             return data if isinstance(data, list) else []
    #     except Exception as e:
    #         logger.error(f" Failed to load scored jobs: {e}")
    #         return []
