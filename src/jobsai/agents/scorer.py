"""
Scorer Service - Job Listing Scoring and Matching.

This module contains the ScorerService class, which scores job listings based
on how well they match the candidate's technology stack. The service computes
relevancy scores (0-100%) by comparing job descriptions against the candidate's
skills and experience.

The scoring process:
1. Flattens the candidate's tech stack into a list of technology names
2. Matches technologies found in job descriptions
3. Calculates match percentage based on matched vs. total technologies
4. Enriches job listings with scores, matched skills, and missing skills
"""

import os
import logging
import json
from typing import List, Dict, Optional, Callable, Any, Union

from jobsai.config.paths import SCORED_JOB_LISTING_PATH
from jobsai.utils.exceptions import CancellationError

from jobsai.utils.normalization import normalize_list

logger = logging.getLogger(__name__)


class ScorerService:
    """Service responsible for scoring job listings against candidate profiles.

    Computes relevancy scores for job listings by matching the candidate's
    technology stack against job descriptions. The scoring is based on:
    - Number of candidate technologies found in the job description
    - Percentage of matched technologies (score = matched / total * 100)

    Each scored job is enriched with:
    - Score (0-100 integer percentage)
    - Matched skills (technologies found in job description)
    - Missing skills (technologies not found in job description)

    Args:
        timestamp (str): Backend-wide timestamp for consistent file naming.
            Format: YYYYMMDD_HHMMSS (e.g., "20250115_143022")
    """

    def __init__(self, timestamp: str) -> None:
        self.timestamp: str = timestamp

    # ------------------------------
    # Public interface
    # ------------------------------
    def score_jobs(
        self,
        raw_jobs: List[Dict[str, Any]],
        tech_stack: List[List[Dict[str, Union[int, str]]]],
        cancellation_check: Optional[Callable[[], bool]] = None,
    ) -> List[Dict[str, Any]]:
        """Score the raw job listings based on the candidate profile.

        Saves the scored jobs to /data/job_listings/scored/{timestamp}_scored_jobs.json.

        Args:
            raw_jobs (List[Dict]): The raw job listings from the searcher.
            tech_stack (List): The candidate tech stack (list of technology categories).
            cancellation_check (Optional[Callable[[], bool]]): Optional callable
                that returns True if the operation should be cancelled. Checked
                periodically during scoring.

        Returns:
            List[Dict]: The scored job listings.

        Raises:
            CancellationError: If cancellation_check returns True during execution
        """

        # Handle empty job list
        if not raw_jobs:
            logger.warning(" No job listings found to score.")
            return []

        # Check for cancellation before starting
        if cancellation_check and cancellation_check():
            logger.info(" Job scoring cancelled by user")
            raise CancellationError("Pipeline cancelled during scoring")

        # Compute scores for all jobs
        scored_jobs = self._compute_scores(raw_jobs, tech_stack, cancellation_check)

        # Sort jobs by score in descending order (highest scores first)
        scored_jobs.sort(key=lambda x: x["score"], reverse=True)

        # Persist scored jobs to disk for debugging and record-keeping
        self._save_scored_jobs(scored_jobs)

        logger.info(
            f" Scored {len(scored_jobs)} jobs to /{SCORED_JOB_LISTING_PATH}/{self.timestamp}_scored_jobs.json"
        )

        return scored_jobs

    # ------------------------------
    # Internal functions
    # ------------------------------

    def _score_job_against_tech_stack(
        self, job: Dict[str, Any], tech_stack: List[str]
    ) -> Dict[str, Any]:
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
        # Combine all job text fields into a single searchable string
        # Includes: title, description snippet, and full description (if deep mode was used)
        # Convert to lowercase for case-insensitive matching
        job_text = " ".join(
            [
                str(job.get("title", "")),
                str(job.get("description_snippet", "")),
                str(job.get("full_description", "")),
            ]
        ).lower()

        # Find technologies from candidate's tech stack that appear in job description
        # Uses simple substring matching (case-insensitive)
        matched_skills = [tech for tech in tech_stack if tech.lower() in job_text]

        # Identify technologies not found in the job description
        missing_skills = [tech for tech in tech_stack if tech.lower() not in job_text]

        # Calculate relevancy score as percentage of matched technologies
        # Formula: (matched_skills / total_skills) * 100
        # Score ranges from 0-100, where 100 means all candidate technologies were found
        # Use max(1, len(tech_stack)) to avoid division by zero
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

    def _compute_scores(
        self,
        raw_jobs: List[Dict[str, Any]],
        tech_stack: List[List[Dict[str, Union[int, str]]]],
        cancellation_check: Optional[Callable[[], bool]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Compute a relevancy score for each job based on the candidate tech stack.

        Args:
            raw_jobs (List[Dict]): The raw job listings from the searcher.
            tech_stack (List): A list of technology categories, where each category
                is a list of dicts with format {technology_name: experience_level}.
                Only technologies with experience_level > 0 are included.
            cancellation_check (Optional[Callable[[], bool]]): Optional callable
                that returns True if the operation should be cancelled.

        Returns:
            List[Dict]: The scored job listings with added score, matched_skills, and missing_skills.

        Raises:
            CancellationError: If cancellation_check returns True during execution
        """
        # Flatten the nested tech_stack structure into a single list of technology names
        # Input structure: List of categories, each containing lists of dicts
        # Example: [{"Python": 7}, {"JavaScript": 6}, ...]
        flattened_tech_stack = []
        for category in tech_stack:
            if isinstance(category, list):
                # Category is a list of technology items
                for item in category:
                    if isinstance(item, dict):
                        # Item is a dict: {technology_name: experience_level}
                        # Extract technology names (keys) from dict
                        for tech_name, experience_level in item.items():
                            # Experience level is an integer (0-7)
                            # 0 = no experience, 1-7 = increasing experience levels
                            if (
                                isinstance(experience_level, int)
                                and experience_level > 0
                            ):
                                # Only include technologies with experience level > 0
                                flattened_tech_stack.append(tech_name)
                            elif isinstance(experience_level, str):
                                # Handle text fields or string values (custom technologies)
                                flattened_tech_stack.append(tech_name)
                    elif isinstance(item, str):
                        # Direct string technology name (fallback format)
                        flattened_tech_stack.append(item)
            elif isinstance(category, str):
                # Category is a direct string (unexpected but handle gracefully)
                flattened_tech_stack.append(category)

        # Normalize the tech stack (deduplicate, standardize capitalization)
        flattened_tech_stack = normalize_list(flattened_tech_stack)

        # Score each job against the tech stack
        scored_jobs = []
        for job in raw_jobs:
            # Check for cancellation before processing each job
            if cancellation_check and cancellation_check():
                logger.info(" Job scoring cancelled by user")
                raise CancellationError("Pipeline cancelled during scoring")

            scored_job = self._score_job_against_tech_stack(job, flattened_tech_stack)
            scored_jobs.append(scored_job)

        return scored_jobs

    def _save_scored_jobs(self, jobs: List[Dict[str, Any]]) -> None:
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
