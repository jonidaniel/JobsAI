"""
Orchestrates the scoring of the raw job listings.

CLASSES:
    ScorerService

FUNCTIONS (in order of workflow):
    score_jobs           (public)
    _compute_scores      (internal)
    _score_job_against_tech_stack (internal)
    _save_scored_jobs    (internal)
"""

import os
import logging
import json
from typing import List, Dict

from jobsai.config.paths import SCORED_JOB_LISTING_PATH

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

    def _compute_scores(self, raw_jobs: List[Dict], tech_stack: List) -> List[Dict]:
        """
        Compute a relevancy score for each job based on the candidate tech stack.

        Args:
            raw_jobs (List[Dict]): The raw job listings from the searcher.
            tech_stack (List): A list of technology categories, where each category
                is a list of dicts with format {technology_name: experience_level}.
                Only technologies with experience_level > 0 are included.

        Returns:
            List[Dict]: The scored job listings with added score, matched_skills, and missing_skills.
        """
        # Flatten tech_stack into a single list of technology names
        # Each category is a list of dicts: [{"Python": 7}, {"JavaScript": 6}, ...]
        flattened_tech_stack = []
        for category in tech_stack:
            if isinstance(category, list):
                for item in category:
                    if isinstance(item, dict):
                        # Extract technology names (keys) from dict
                        # Only include technologies with experience level > 0
                        for tech_name, experience_level in item.items():
                            # Experience level is an integer (0-7), 0 means no experience
                            if (
                                isinstance(experience_level, int)
                                and experience_level > 0
                            ):
                                flattened_tech_stack.append(tech_name)
                            elif isinstance(experience_level, str):
                                # Handle text fields or string values
                                flattened_tech_stack.append(tech_name)
                    elif isinstance(item, str):
                        # Direct string technology name
                        flattened_tech_stack.append(item)
            elif isinstance(category, str):
                flattened_tech_stack.append(category)

        # Normalize the tech stack (deduplicate, standardize capitalization)
        flattened_tech_stack = normalize_list(flattened_tech_stack)

        # Score each job against the tech stack
        scored_jobs = []
        for job in raw_jobs:
            scored_job = self._score_job_against_tech_stack(job, flattened_tech_stack)
            scored_jobs.append(scored_job)

        return scored_jobs

    # ------------------------------
    # Public interface
    # ------------------------------
    def score_jobs(self, raw_jobs: List[Dict], tech_stack: List) -> List[Dict]:
        """Score the raw job listings based on the candidate profile.

        Saves the scored jobs to /data/job_listings/scored/{timestamp}_scored_jobs.json.

        Args:
            raw_jobs (List[Dict]): The raw job listings from the searcher.
            tech_stack (List): The candidate tech stack (list of technology categories).

        Returns:
            List[Dict]: The scored job listings.
        """

        if not raw_jobs:
            logger.warning(" No job listings found to score.")
            return

        scored_jobs = self._compute_scores(raw_jobs, tech_stack)

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

    def _score_job_against_tech_stack(self, job: Dict, tech_stack: List[str]) -> Dict:
        """
        Score a single job against a tech stack.

        Args:
            job (Dict): The job listing dictionary containing:
                - "title": Job title
                - "description_snippet": Short description from search results
                - "full_description": Full job description (if deep mode was used)
            tech_stack (List[str]): The flattened list of technology names to match.

        Returns:
            Dict: The job dictionary with added fields:
                - "score": Integer score (0-100) representing match percentage
                - "matched_skills": The list of technologies found in the job description
                - "missing_skills": The list of technologies not found in the job description
        """
        # Combine all job text into a single searchable string
        # Includes title, snippet, and full description (if available)
        job_text = " ".join(
            [
                str(job.get("title", "")),
                str(job.get("description_snippet", "")),
                str(job.get("full_description", "")),
            ]
        ).lower()

        # Find which technologies from the tech stack appear in the job description
        matched_skills = [tech for tech in tech_stack if tech.lower() in job_text]
        # Compute missing skills as technologies not found in job description
        missing_skills = [tech for tech in tech_stack if tech.lower() not in job_text]

        # Calculate score as percentage of matched technologies
        # Score ranges from 0-100, where 100 means all technologies were found
        score = int(len(matched_skills) / max(1, len(tech_stack)) * 100)

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
