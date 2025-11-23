# ---------- REPORTER AGENT ----------

import os
import logging
import json
from typing import List, Dict

logger = logging.getLogger(__name__)

class ReporterAgent:
    """
    ReporterAgent class orchestrates reporting job findings.

    Responsibilities:
    1. Load scored job listings
    2. Write a report/an analysis of the scored job listings
    """

    def __init__(self, jobs_scored_path: str, reports_path: str):
        """
        Construct the ReporterAgent class.

        Args:
            jobs_scored_path:
            reports_path:
        """

        self.jobs_scored_path = jobs_scored_path
        self.reports_path = reports_path

    # ------------------------------
    # Public interface
    # ------------------------------
    def generate_report(self, top_n: int = 10) -> str:
        """
        Load scored jobs, generate a summary report (text),
        save it to REPORTS_DIR, and return the report text.

        Args:
            top_n: the number of top jobs to include

        Returns:
            report_text: the generated report as a string
        """

        logger.info(" WRITING JOB LISTINGS REPORT STARTING...")

        scored_jobs = self.load_scored_jobs()
        if not scored_jobs:
            logger.warning(" No scored jobs found for reporting.")
            return ""

        # Sort jobs by score descending (already done in scorer, but safe)
        scored_jobs.sort(key=lambda x: x.get("score", 0), reverse=True)

        report_lines = ["Job Report", "=" * 40, f"Top {top_n} Jobs:\n"]

        for job in scored_jobs[:top_n]:
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
            report_lines.append("-" * 40)

        report_text = "\n".join(report_lines)

        # Save report to file
        filename = f"job_report.txt"
        path = os.path.join(self.reports_path, filename)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(report_text)

            logger.info(f" WRITING JOB LISTINGS REPORT COMPLETED: Report saved to /{path} successfully\n")
        except Exception as e:
            logger.info(f" WRITING JOB LISTINGS REPORT FAILED: {e}\n")

        return report_text

    # ------------------------------
    # Internal function
    # ------------------------------
    def load_scored_jobs(self) -> List[Dict]:
        """
        Load scored jobs JSON from SCORED_JOB_LISTINGS_DIR.

        Returns:
            []:
            data:
        """

        path = os.path.join(self.jobs_scored_path, "scored_jobs.json")
        if not os.path.exists(path):
            return []

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f" Failed to load scored jobs: {e}")
            return []
