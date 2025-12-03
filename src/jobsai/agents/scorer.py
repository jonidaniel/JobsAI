"""
Orchestrates the scoring of the raw job listings.

CLASSES:
    ScorerService

FUNCTIONS (in order of workflow):
    1. score_jobs           (public use)
    2. _compute_job_score   (internal use)
    3. _save_scored_jobs    (internal use)
"""

import os
import logging
import json
from typing import List, Dict

from jobsai.config.paths import SCORED_JOB_LISTING_PATH
from jobsai.config.schemas import SkillProfile

from jobsai.utils.normalization import normalize_list

logger = logging.getLogger(__name__)


class ScorerService:
    """Orchestrates the scoring of the raw job listings.

    Responsibilities:
    1. Compute a relevancy score for a job based on the candidate profile
    2. Enrich the job listing with the score and the matched/missing skills
    3. Save the scored job listings

    Args:
        timestamp (str): The backend-wide timestamp of the moment when the main function was started.
    """

    def __init__(self, timestamp: str):
        self.timestamp = timestamp

    # ------------------------------
    # Public interface
    # ------------------------------
    def score_jobs(self, raw_jobs: List[Dict], profile: SkillProfile) -> List[Dict]:
        """Score the raw job listings based on the candidate profile.

        Saves the scored jobs to /data/job_listings/scored/{timestamp}_scored_jobs.json.

        Args:
            raw_jobs (List[Dict]): The raw job listings from the searcher.
            profile (SkillProfile): The candidate profile.

        Returns:
            List[Dict]: The scored job listings.
        """

        # THIS IS NOT NEEDED SINCE WE ARE PASSING THE RAW JOBS DIRECTLY
        # job_listings = self._load_job_listings()

        if not raw_jobs:
            logger.warning(" No job listings found to score.")
            return

        scored_jobs = [self._compute_job_score(job, profile) for job in raw_jobs]
        # Sort by score descending
        scored_jobs.sort(key=lambda x: x["score"], reverse=True)

        # Save only for safety
        self._save_scored_jobs(scored_jobs)

        logger.info(
            f" Scored {len(scored_jobs)} jobs to /{SCORED_JOB_LISTING_PATH}/{self.timestamp}_scored_jobs.json"
        )

        return scored_jobs

    # ------------------------------
    # Internal functions
    # ------------------------------

    def _compute_job_score(self, job: Dict, profile: SkillProfile) -> Dict:
        """
        Compute a relevancy score for a job based on the candidate profile.

        Scoring algorithm:
        1. Extract all skill keywords from the candidate's profile
        2. Search for these keywords in the job description (title, snippet, full description)
        3. Calculate score as percentage of matched skills
        4. Return job dict enriched with score and matched/missing skills lists

        Args:
            job (Dict): The job listing dictionary containing:
                - "title": Job title
                - "description_snippet": Short description from search results
                - "full_description": Full job description (if deep mode was used)
            profile (SkillProfile): The candidate profile.

        Returns:
            Dict: The job dictionary with added fields:
                - "score": Integer score (0-100) representing match percentage
                - "matched_skills": The list of profile skills found in the job description
                - "missing_skills": The list of profile skills not found in the job description
        """

        # Combine all skill keywords from all profile categories
        # This creates a comprehensive list of skills to search for
        profile_keywords = (
            profile.core_languages
            + profile.frameworks_and_libraries
            + profile.tools_and_platforms
            + profile.agentic_ai_experience
            + profile.ai_ml_experience
            + profile.soft_skills
            + profile.projects_mentioned
            + profile.job_search_keywords
        )
        # Normalize keywords (deduplicate, standardize capitalization)
        profile_keywords = normalize_list(profile_keywords)

        # Combine all job text into a single searchable string
        # Includes title, snippet, and full description (if available)
        job_text = " ".join(
            [
                str(job.get("title", "")),
                str(job.get("description_snippet", "")),
                str(job.get("full_description", "")),
            ]
        ).lower()

        # Find which profile skills appear in the job description
        matched_skills = [kw for kw in profile_keywords if kw.lower() in job_text]
        missing_skills = [kw for kw in profile_keywords if kw.lower() not in job_text]

        # Calculate score as percentage of matched skills
        # Score ranges from 0-100, where 100 means all profile skills were found
        score = int(len(matched_skills) / max(1, len(profile_keywords)) * 100)

        # Enrich job dict with scoring information
        scored_job = job.copy()
        scored_job.update(
            {
                "score": score,
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
            }
        )
        return scored_job

    def _save_scored_jobs(self, jobs: List[Dict]):
        """Save the scored jobs.

        Saves to /data/job_listings/scored/{timestamp}_scored_jobs.json.

        Args:
            jobs (List[Dict]): The scored job listings.
        """

        if not jobs:
            return

        # Form a dated filename and make a path
        filename = f"{self.timestamp}_scored_jobs.json"
        path = os.path.join(SCORED_JOB_LISTING_PATH, filename)

        # Save to the path
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(jobs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f" Failed to save scored jobs: {e}")

    # def _load_job_listings(self) -> List[Dict]:
    #     """Load the raw job listings.

    #     Loads all JSON files from /src/jobsai/data/job_listings/raw and returns them as a list.

    #     Returns:
    #         List[Dict]: The list of raw job listings.
    #     """

    #     jobs = []
    #     for filename in os.listdir(RAW_JOB_LISTING_PATH):
    #         if not filename.endswith(".json"):
    #             continue
    #         path = os.path.join(RAW_JOB_LISTING_PATH, filename)
    #         try:
    #             with open(path, "r", encoding="utf-8") as file:
    #                 job_listings_data = json.load(file)
    #                 if isinstance(job_listings_data, list):
    #                     jobs.extend(job_listings_data)
    #         except Exception as e:
    #             logger.error(f" Failed to load {path}: {e}")
    #     # Deduplicate by URL (falling back to lightweight fingerprint when URL missing)
    #     seen_fingerprints = set()
    #     unique_jobs = []
    #     for job in jobs:
    #         fingerprint = self._job_identity(job)
    #         if fingerprint and fingerprint not in seen_fingerprints:
    #             unique_jobs.append(job)
    #             seen_fingerprints.add(fingerprint)
    #     return unique_jobs

    # @staticmethod
    # def _job_identity(job: Dict) -> str:
    #     """Build a repeatable identifier for a job.

    #     Prefer URL, otherwise a hashable combo of fields that tends to be stable across scrapes.

    #     Args:
    #         job (Dict): The job listing dictionary.

    #     Returns:
    #         str: The job identifier.
    #     """
    #     # Try to use the URL as the identifier
    #     url = (job.get("url") or "").strip()
    #     # If the URL is not empty, return it
    #     if url:
    #         return url

    #     title = (job.get("title") or "").strip().lower()
    #     query = (job.get("query_used") or "").strip().lower()
    #     snippet = (job.get("description_snippet") or "").strip().lower()
    #     if not title and not query and not snippet:
    #         return ""
    #     # Limit snippet length to keep keys short while remaining distinctive
    #     snippet_prefix = snippet[:80]
    #     return f"{title}|{query}|{snippet_prefix}"
