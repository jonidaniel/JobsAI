# ---------- SEARCHER AGENT ----------

import os
import logging
import json

from typing import List, Dict

from utils import build_queries
from utils import fetch_search_results

# Logging configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class SearcherAgent:
    """
    SearcherAgent orchestrates job search using a skill profile.

    Responsibilities:
    1. Build queries from skill profile
    2. Fetch job listings from supported job boards
    3. Deduplicate listings
    4. Save raw JSON for inspection
    """

    def __init__(self, job_boards: List[str] = None, deep: bool = True, save_path: str = "data/job_listings/raw"):
        self.job_boards = job_boards or ["duunitori"]
        self.deep = deep
        self.save_path = save_path
        os.makedirs(self.save_path, exist_ok=True)

    # ------------------------------
    # Public interface
    # ------------------------------
    def search_jobs(self, skill_profile: dict) -> List[Dict]:
        """
        Run searches on all job boards using queries from the skill profile.
        Returns a deduplicated list of jobs.
        """

        all_jobs = []
        queries = build_queries(skill_profile)

        for query in queries:
            for board in self.job_boards:
                logger.info("Searching %s for query '%s'", board, query)
                if board.lower() == "duunitori":
                    jobs = fetch_search_results(query, deep=self.deep)
                else:
                    # Placeholder for other boards
                    jobs = []

                all_jobs.extend(jobs)
                self._save_raw_jobs(jobs, board, query)

        return self._deduplicate_jobs(all_jobs)

    # ------------------------------
    # Internal functions
    # ------------------------------

    def _deduplicate_jobs(self, jobs: List[Dict]) -> List[Dict]:
        seen_urls = set()
        deduped = []
        for job in jobs:
            url = job.get("url")
            if url and url not in seen_urls:
                deduped.append(job)
                seen_urls.add(url)
        return deduped

    def _save_raw_jobs(self, jobs: List[Dict], board: str, query: str):
        if not jobs:
            return
        safe_query = query.replace(" ", "_").replace("/", "_")
        filename = f"{board}_{safe_query}.json"
        path = os.path.join(self.save_path, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
        logger.info("Saved %d raw jobs to %s", len(jobs), path)

# ------------------------------
# Simple CLI usage
# ------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run SearcherAgent using a skill profile JSON.")
    parser.add_argument("profile", help="Path to skill profile JSON")
    parser.add_argument("--deep", action="store_true", help="Fetch full job descriptions")
    args = parser.parse_args()

    if not os.path.exists(args.profile):
        raise FileNotFoundError(f"Skill profile not found: {args.profile}")

    with open(args.profile, "r", encoding="utf-8") as f:
        skill_profile = json.load(f)

    agent = SearcherAgent(deep=args.deep)
    jobs = agent.search_jobs(skill_profile)
    print(f"Found {len(jobs)} unique jobs.")
