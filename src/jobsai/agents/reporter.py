# ---------- REPORTER AGENT ----------

# generate_report
# _load_scored_jobs

import os
import logging
import json
from pathlib import Path
from typing import List, Dict

from config.schemas import SkillProfile
from utils.llms import call_llm

logger = logging.getLogger(__name__)


class ReporterAgent:
    """
    ReporterAgent class orchestrates reporting job findings.

    Responsibilities:
    1. Load scored job listings
    2. Write a report/an analysis of the scored job listings
    """

    def __init__(self, jobs_scored_path: Path, reports_path: Path, timestamp: str):
        """
        Construct the ReporterAgent class.

        Args:
            jobs_scored_path:
            reports_path:
        """

        self.jobs_scored_path = jobs_scored_path
        self.reports_path = reports_path
        self.timestamp = timestamp

    # ------------------------------
    # Public interface
    # ------------------------------
    def generate_report(
        self, skill_profile: SkillProfile, report_size: int = 10
    ) -> str:
        """
        Load scored jobs, generate a summary report (text),
        save it to REPORTS_DIR, and return the report text.

        Args:
            report_size: the number of top jobs to include

        Returns:
            report_text: the generated report as a string
        """

        logger.info(" WRITING JOB LISTINGS REPORT...")

        scored_jobs = self._load_scored_jobs()
        if not scored_jobs:
            logger.warning(" No scored jobs found for reporting.")
            return ""

        # Sort jobs by score descending (already done in scorer, but safe)
        scored_jobs.sort(key=lambda x: x.get("score", 0), reverse=True)

        report_lines = ["Job Report", "=" * 40, f"Top {report_size} Jobs:\n"]

        for job in scored_jobs[:report_size]:
            #

            full_description = job.get("full_description")

            system_prompt = """
            You are an expert on planning cover letters to be attached to job applications.
            You base your plans on job descriptions and candidates' skill profiles."
            """

            user_prompt = f"""
            Here is a job description:
            \"\"\"
            {full_description}
            \"\"\"

            And here is a candidate's skill profile:
            \"\"\"
            {skill_profile}
            \"\"\"

            Your job is to give instructions on what kind of a cover letter should be written to get the job.
            Note that an LLM writes the cover letter, and the instructions are intended as 'user prompt' for an LLM.
            Do not include a 'system prompt'.
            The instructions should be ready to be given to an LLM 'as is', without any modifications.
            A human will not read the instructions.

            The instructions should contain only the actual instructions.
            The instructions should focus on the actual cover letter contents/text paragraphs.
            The instructions should be based on the job description and the candidate's skill profile.
            The instructions should be tailored for the specific candidate.
            The instructions should emphasize matches between the candidate's skills and the job's skill requirements.
            The instructions should not include any fluff or meta information.
            The instructions should not include any suggestions on how to format the letter.

            Write the instructions.
            """

            # Generate instructions to write a cover letter
            instructions = call_llm(system_prompt, user_prompt)

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

        # Form a dated filename
        filename = f"{self.timestamp}_job_report.txt"

        # Join the report path and the dated filename
        path = os.path.join(self.reports_path, filename)

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(report_text)

            logger.info(f" JOB LISTINGS REPORT WRITTEN: Report saved to /{path}\n")
        except Exception as e:
            logger.error(f" WRITING JOB LISTINGS REPORT FAILED: {e}\n")

        return report_text

    # ------------------------------
    # Internal function
    # ------------------------------
    def _load_scored_jobs(self) -> List[Dict]:
        """
        Load scored jobs JSON from SCORED_JOB_LISTINGS_DIR.

        Returns:
            []:
            data:
        """

        path = os.path.join(self.jobs_scored_path, f"{self.timestamp}_scored_jobs.json")
        if not os.path.exists(path):
            return []

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f" Failed to load scored jobs: {e}")
            return []
