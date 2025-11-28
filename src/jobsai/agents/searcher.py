"""
JobsAI/src/jobsai/agents/searcher.py

Acts as the SEARCHER AGENT.

CLASSES:
    SearcherAgent

FUNCTIONS (in order of workflow):
    1. SearcherAgent.search_jobs          (public use)
    2. SearcherAgent._save_raw_jobs       (internal use)
    3. SearcherAgent._deduplicate_jobs    (internal use)
"""

import os
import logging
import json
from pathlib import Path
from typing import List, Dict

from jobsai.utils.scrapers.duunitori import scrape_duunitori
from jobsai.utils.scrapers.jobly import scrape_jobly
from jobsai.utils.queries import build_queries

logger = logging.getLogger(__name__)


class SearcherAgent:
    """Orchestrate the job listings search.

    Responsibilities:
    1. Build queries from skill profile
    2. Fetch job listings from supported job boards
    3. Deduplicate the job listings
    4. Store the job listings

    Args:
        job_boards (List[str]):
        deep_mode (bool):
        jobs_raw_path (Path):
        timestamp (str): The backend-wide timestamp of the moment when the main function was started.
    """

    def __init__(
        self,
        job_boards: List[str],
        deep_mode: bool,
        jobs_raw_path: Path,
        timestamp: str,
    ):
        self.job_boards = job_boards
        self.deep_mode = deep_mode
        self.jobs_raw_path = jobs_raw_path
        self.timestamp = timestamp

    # ------------------------------
    # Public interface
    # ------------------------------
    def search_jobs(self, skill_profile: dict) -> List[Dict]:
        """Run searches on all job boards using queries from the skill profile.

        Args:
            skill_profile (dict): HUOM DICT

        Returns:
            callable: A deduplicated list of jobs.
        """

        logger.info(" WEB SCRAPING STARTING...")

        all_jobs = []

        # Build deterministic job search queries from a structured skill profile
        queries = build_queries(skill_profile)

        for query in queries:
            # Iterate over all job boards (duunitori, jobly, etc.) defined in /config/settings.py
            for job_board in self.job_boards:
                print()
                logger.info(" Searching %s for query '%s'", job_board, query)
                if job_board.lower() == "duunitori":
                    jobs = scrape_duunitori(query, deep_mode=self.deep_mode)
                else:
                    # Placeholder for other boards
                    jobs = []

                all_jobs.extend(jobs)
                self._save_raw_jobs(jobs, job_board, query)

        print()
        logger.info(" WEB SCRAPING COMPLETED\n")

        return self._deduplicate_jobs(all_jobs)

    # ------------------------------
    # Internal functions
    # ------------------------------

    def _save_raw_jobs(self, jobs: List[Dict], board: str, query: str):
        """Save raw job listings to src/jobsai/data/job_listings/raw/

        Args:
            jobs (List[Dict]):
            board (str):
            query (str):
        """

        if not jobs:
            return

        # Replace spaces and forward slashed with underscores
        safe_query = query.replace(" ", "_").replace("/", "_")

        # Form the filename (<job_board><query>.json)
        filename = f"{self.timestamp}_{board.lower()}_{safe_query}.json"

        # Form the path where to save
        path = os.path.join(self.jobs_raw_path, filename)

        # Save to the path
        with open(path, "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)

        logger.info(" Saved %d raw jobs to /%s", len(jobs), path)

    def _deduplicate_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Remove duplicate the job listings.

        Args:
            jobs (List[Dict]):

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
