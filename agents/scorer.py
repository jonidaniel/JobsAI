# ---------- SCORER AGENT ----------

import os
import json
from typing import List, Dict

from utils import normalize_list

from config.schemas import SkillProfile

class ScorerAgent:
    def __init__(self, jobs_raw_path, jobs_scored_path):
        self.jobs_raw_path = jobs_raw_path
        self.jobs_scored_path = jobs_scored_path
        os.makedirs(jobs_raw_path, exist_ok=True)

    # ------------------------------
    # Public interface
    # ------------------------------
    def score_jobs(self, skill_profile: SkillProfile) -> None:
        """
        Fetch all raw job listings from /data/job_listings/,
        score them based on the given skill profile, and save
        scored jobs to SCORED_JOB_LISTINGS_DIR.
        """
        job_listings = self.load_job_listings()
        if not job_listings:
            print("No job listings found to score.")
            return

        scored_jobs = [self.compute_job_score(job, skill_profile) for job in job_listings]
        # Sort by score descending
        scored_jobs.sort(key=lambda x: x["score"], reverse=True)
        self.save_scored_jobs(scored_jobs)
        print(f"Scored {len(scored_jobs)} jobs and saved to {self.jobs_scored_path}")

    # ------------------------------
    # Internal functions
    # ------------------------------

    def load_job_listings(self) -> List[Dict]:
        """
        Load all JSON files from RAW_JOB_LISTINGS_DIR and return as a list of jobs.
        """
        jobs = []
        for f in os.listdir(self.jobs_raw_path):
            if not f.endswith(".json"):
                continue
            path = os.path.join(self.jobs_raw_path, f)
            try:
                with open(path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    if isinstance(data, list):
                        jobs.extend(data)
            except Exception as e:
                print(f"Failed to load {path}: {e}")
        # Deduplicate by URL (falling back to lightweight fingerprint when URL missing)
        seen = set()
        unique_jobs = []
        for job in jobs:
            fingerprint = self._job_identity(job)
            if fingerprint and fingerprint not in seen:
                unique_jobs.append(job)
                seen.add(fingerprint)
        return unique_jobs

    def compute_job_score(self, job: Dict, skill_profile: SkillProfile) -> Dict:
        """
        Compute a simple matching score for the job based on the skill profile.
        """
        # Combine all skill keywords from the profile
        profile_keywords = (
            skill_profile.core_languages +
            skill_profile.frameworks_and_libraries +
            skill_profile.tools_and_platforms +
            skill_profile.agentic_ai_experience +
            skill_profile.ai_ml_experience +
            skill_profile.soft_skills +
            skill_profile.projects_mentioned +
            skill_profile.job_search_keywords
        )
        profile_keywords = normalize_list(profile_keywords)

        job_text = " ".join([
            str(job.get("title", "")),
            str(job.get("description_snippet", "")),
            str(job.get("full_description", ""))
        ]).lower()

        matched_skills = [kw for kw in profile_keywords if kw.lower() in job_text]
        missing_skills = [kw for kw in profile_keywords if kw.lower() not in job_text]

        # Simple scoring: percentage of matched skills
        score = int(len(matched_skills) / max(1, len(profile_keywords)) * 100)

        job_copy = job.copy()
        job_copy.update({
            "score": score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills
        })
        return job_copy

    def save_scored_jobs(self, scored_jobs: List[Dict]):
        """
        Save scored jobs into SCORED_JOB_LISTINGS_DIR as a JSON file.
        """
        if not scored_jobs:
            return
        filename = f"scored_jobs.json"
        path = os.path.join(self.jobs_scored_path, filename)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(scored_jobs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save scored jobs: {e}")

    @staticmethod
    def _job_identity(job: Dict) -> str:
        """
        Build a repeatable identifier for a job. Prefer URL, otherwise a hashable
        combo of fields that tends to be stable across scrapes.
        """
        url = (job.get("url") or "").strip()
        if url:
            return url

        title = (job.get("title") or "").strip().lower()
        query = (job.get("query_used") or "").strip().lower()
        snippet = (job.get("description_snippet") or "").strip().lower()
        if not title and not query and not snippet:
            return ""
        # Limit snippet length to keep keys short while remaining distinctive.
        snippet_prefix = snippet[:80]
        return f"{title}|{query}|{snippet_prefix}"
