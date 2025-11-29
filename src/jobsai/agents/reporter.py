"""
JobsAI/src/jobsai/agents/reporter.py

Acts as the REPORTER AGENT.

CLASSES:
    ReporterAgent

FUNCTIONS (in order of workflow):
    1. ReporterAgent.generate_report      (public use)
    2. ReporterAgent._load_scored_jobs    (internal use)
"""

import os
import logging
import json
from typing import List, Dict

from jobsai.config.paths import SCORED_JOB_LISTING_PATH, JOB_REPORT_PATH
from jobsai.config.prompts import (
    REPORTER_SYSTEM_PROMPT as SYSTEM_PROMPT,
    REPORTER_USER_PROMPT as USER_PROMPT,
)
from jobsai.config.schemas import SkillProfile

from jobsai.utils.llms import call_llm

logger = logging.getLogger(__name__)


class ReporterAgent:
    """Orchestrates the reporting of the best-scored jobs.

    Responsibilities:
    1. Load scored job listings
    2. Write a report/an analysis of the scored job listings

    Args:
        timestamp (str): The backend-wide timestamp of the moment when the main function was started.
    """

    def __init__(self, timestamp: str):
        self.timestamp = timestamp

    # ------------------------------
    # Public interface
    # ------------------------------
    def generate_report(self, skill_profile: SkillProfile, report_size: int) -> str:
        """Generate a summary report on the most-scored jobs.

        Saves it to src/jobsai/data/job_reports/ and also returns the job report.

        Args:
            report_size (int): The desired number of top jobs to include in the report.

        Returns:
            str: The job report.
        """

        logger.info(" WRITING JOB REPORT ...")

        scored_jobs = self._load_scored_jobs()
        if not scored_jobs:
            logger.warning(" No scored jobs found for reporting.")
            return ""

        # Sort jobs by score descending (already done in scorer, but safe)
        scored_jobs.sort(key=lambda x: x.get("score", 0), reverse=True)

        # ????
        report_lines = ["Job Report", "=" * 40, f"Top {report_size} Jobs:\n"]

        for job in scored_jobs[:report_size]:
            full_description = job.get("full_description")

            # Generate instructions on what kind of cover letter to write
            instructions = call_llm(
                SYSTEM_PROMPT,
                USER_PROMPT.format(
                    full_description=full_description,
                    skill_profile=skill_profile,
                ),
            )

            title = job.get("title") or "N/A"
            company = job.get("company") or "N/A"
            location = job.get("location") or "N/A"
            score = job.get("score", 0)
            matched = ", ".join(job.get("matched_skills", []))
            missing = ", ".join(job.get("missing_skills", []))
            url = job.get("url") or "N/A"

            report_lines.append(f"Title: {title}")
            report_lines.append(f"Company: {company}")
            report_lines.append(f"Location: {location}")
            report_lines.append(f"Score: {score}%")
            report_lines.append(f"Matched Skills: {matched}")
            report_lines.append(f"Missing Skills: {missing}")
            report_lines.append(f"URL: {url}")
            report_lines.append(f"Instructions: {instructions}")
            report_lines.append("-" * 40)

        report_text = "\n".join(report_lines)

        # Form a dated filename and join it with the report path
        filename = f"{self.timestamp}_job_report.txt"
        path = os.path.join(JOB_REPORT_PATH, filename)

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(report_text)

            logger.info(f" JOB REPORT SAVED TO /{path}\n")
        except Exception as e:
            logger.error(f" JOB REPORT FAILED: {e}\n")

        return report_text

    # ------------------------------
    # Internal function
    # ------------------------------
    def _load_scored_jobs(self) -> List[Dict]:
        """Load the scored job listings from src/jobsai/data/job_listings/scored/.

        Returns:
            List[Dict]: The
        """

        path = os.path.join(
            SCORED_JOB_LISTING_PATH, f"{self.timestamp}_scored_jobs.json"
        )
        if not os.path.exists(path):
            return []

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f" Failed to load scored jobs: {e}")
            return []
