"""
Orchestrate the job listings search.

CLASSES:
    SearcherService

FUNCTIONS (in order of workflow):
    1. search_jobs          (public use)
    2. _save_raw_jobs       (internal use)
    3. _deduplicate_jobs    (internal use)
"""

import os
import logging
import json
from typing import List, Dict

from jobsai.config.paths import RAW_JOB_LISTING_PATH

from jobsai.utils.scrapers.duunitori import scrape_duunitori
from jobsai.utils.scrapers.jobly import scrape_jobly
from jobsai.utils.queries import build_queries

logger = logging.getLogger(__name__)


class SearcherService:
    """Orchestrate the job listings search.

    Responsibilities:
    1. Build queries from skill profile
    2. Fetch job listings from supported job boards
    3. Deduplicate the job listings
    4. Store the job listings

    Args:
        job_boards (List[str]): The job boards to search.
        deep_mode (bool): If True, fetch each job's detail page to extract the full description.
        timestamp (str): The backend-wide timestamp for consistent file naming.
    """

    def __init__(
        self,
        job_level: str,
        job_boards: List[str],
        deep_mode: bool,
        timestamp: str,
    ):
        self.job_level = job_level
        self.job_boards = job_boards
        self.deep_mode = deep_mode
        self.timestamp = timestamp

    # ------------------------------
    # Public interface
    # ------------------------------
    def search_jobs(self, skill_profile: dict) -> List[Dict]:
        """Run searches on all job boards using queries from the skill profile.

        Args:
            skill_profile (dict): The skill profile.

        Returns:
            List[Dict]: The deduplicated list of jobs.
        """

        all_jobs = []

        # Build deterministic job search queries
        queries = build_queries(skill_profile)

        for query in queries:
            for job_board in self.job_boards:
                print()
                logger.info(" Searching %s for query '%s'", job_board, query)
                # User sends through UI which job board to use

                if job_board.lower() == "duunitori":
                    jobs = scrape_duunitori(query, deep_mode=self.deep_mode)
                elif job_board.lower() == "jobly":
                    jobs = scrape_jobly(query, deep_mode=self.deep_mode)
                else:
                    # Placeholder for other boards
                    jobs = []

                all_jobs.extend(jobs)
                self._save_raw_jobs(jobs, job_board, query)

        return self._deduplicate_jobs(all_jobs)

    # ------------------------------
    # Internal functions
    # ------------------------------

    def _save_raw_jobs(self, jobs: List[Dict], board: str, query: str):
        """Save raw job listings.

        Saves to RAW_JOB_LISTING_PATH.

        Args:
            jobs (List[Dict]): The job listings.
            board (str): The job board name, used for filename.
            query (str): The query, used for filename.
        """

        if not jobs:
            return

        # Replace spaces and forward slashed with underscores
        safe_query = query.replace(" ", "_").replace("/", "_")

        # Form the filename (<job_board><query>.json)
        filename = f"{self.timestamp}_{board.lower()}_{safe_query}.json"

        # Form the path where to save
        path = os.path.join(RAW_JOB_LISTING_PATH, filename)

        # Save to the path
        with open(path, "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)

        logger.info(" Saved %d raw jobs to /%s", len(jobs), path)

    def _deduplicate_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Remove duplicate the job listings.

        Args:
            jobs (List[Dict]): The job listings.

        Returns:
            List[Dict]: The deduplicated list of jobs.
        """

        seen_urls = set()
        deduped = []

        for job in jobs:
            url = job.get("url")
            if url and url not in seen_urls:
                deduped.append(job)
                seen_urls.add(url)
        return deduped
