# ---------- SEARCHER AGENT ----------

import os
import logging
import json
from typing import List, Dict

from utils import build_queries, fetch_search_results

logger = logging.getLogger(__name__)

class SearcherAgent:
    """
    SearcherAgent orchestrates job search using a skill profile.

    Responsibilities:
    1. Build queries from skill profile
    2. Fetch job listings from supported job boards
    3. Deduplicate listings
    4. Save raw JSON for inspection
    """

    def __init__(self, job_boards: List[str], deep_mode: bool, jobs_raw_path: str):
        """
        Initialize searcher agent

        Args:
            job_boards:
            deep_mode:
            jobs_raw_path:
        """

        self.job_boards = job_boards
        self.deep_mode = deep_mode
        self.jobs_raw_path = jobs_raw_path

    # ------------------------------
    # Public interface
    # ------------------------------
    def search_jobs(self, skill_profile: dict) -> List[Dict]:
        """
        Run searches on all job boards using queries from the skill profile

        Args:
            skill_profile:

        Returns:
            self._deduplicate_jobs(all_jobs): deduplicated list of jobs
        """

        logger.info(" WEB SCRAPING STARTING...\n")

        all_jobs = []

        # Build deterministic job search queries from a structured skill profile
        queries = build_queries(skill_profile)

        for query in queries:
            # Iterate over all job boards (duunitori, jobly, etc.) defined in /config/settings.py
            for job_board in self.job_boards:
                logger.info(" Searching %s for query '%s'", job_board, query)
                if job_board.lower() == "duunitori":
                    jobs = fetch_search_results(query, deep_mode=self.deep_mode)
                else:
                    # Placeholder for other boards
                    jobs = []

                all_jobs.extend(jobs)
                self._save_raw_jobs(jobs, job_board, query)

        logger.info(" WEB SCRAPING COMPLETED\n")

        return self._deduplicate_jobs(all_jobs)

    # ------------------------------
    # Internal functions
    # ------------------------------

    def _deduplicate_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """
        Remove duplicate job listings

        Args:
            jobs:

        Returns:
            deduped: deduplicated list of jobs
        """

        seen_urls = set()
        deduped = []


        for job in jobs:
            url = job.get("url")
            if url and url not in seen_urls:
                deduped.append(job)
                seen_urls.add(url)
        return deduped

    def _save_raw_jobs(self, jobs: List[Dict], board: str, query: str):
        """
        Save raw job listings to /data/job_listings/raw/

        Args:
            jobs:
            board:
            query:
        """

        if not jobs:
            return
        safe_query = query.replace(" ", "_").replace("/", "_")
        filename = f"{board}_{safe_query}.json"
        path = os.path.join(self.jobs_raw_path, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
        logger.info(" Saved %d raw jobs to /%s\n", len(jobs), path)
