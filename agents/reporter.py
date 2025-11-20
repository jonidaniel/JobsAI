import os
import json
from typing import List, Dict

SCORED_JOB_LISTINGS_DIR = "data/job_listings/scored"
REPORTS_DIR = "data/reports"

class ReporterAgent:
    def __init__(self):
        os.makedirs(REPORTS_DIR, exist_ok=True)

    # -----------------------------
    # Public interface
    # -----------------------------
    def generate_report(self, top_n: int = 10) -> str:
        """
        Load scored jobs, generate a summary report (text),
        save it to REPORTS_DIR, and return the report text.
        """
        scored_jobs = self.load_scored_jobs()
        if not scored_jobs:
            print("No scored jobs found for reporting.")
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
        path = os.path.join(REPORTS_DIR, filename)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(report_text)
            print(f"Report saved to {path}")
        except Exception as e:
            print(f"Failed to save report: {e}")

        return report_text

    # -----------------------------
    # Internal helpers
    # -----------------------------
    def load_scored_jobs(self) -> List[Dict]:
        """
        Load scored jobs JSON from SCORED_JOB_LISTINGS_DIR.
        """
        path = os.path.join(SCORED_JOB_LISTINGS_DIR, "scored_jobs.json")
        if not os.path.exists(path):
            return []

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            print(f"Failed to load scored jobs: {e}")
            return []
