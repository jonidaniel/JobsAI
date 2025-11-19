# ---------- SEARCHER AGENT ----------

# 1. Takes the skill profile produced by the Skill Assessment agent
# 2. Converts it into search queries
# 3. Scrapes Finnish job sites
# 4. Parses the results into a normalized job listing schema
# 5. Saves listings under /data/job_listings/raw/ and /processed/
# 6. Returns structured listings to the Planner / Scorer agent

# This is the LLM-based orchestrator for job search:
# 1. Receives:
# • Skills profile (JSON)
# • Search settings (max listings, max sites, etc.)
# 2. Decides:
# • Which keywords to search
# • Which sites to use
# • How many results to fetch
# • Whether narrowing or expanding queries is needed
# 3. Instructs scraper functions to run
# 4. Returns:
# • Normalized list of job postings
# • Saved raw job JSON under /data/job_listings/
# • Metadata about the search (query coverage, failure logs)

import os
import json

from typing import List, Dict
from utils.query_builder import build_queries
from utils.scraper_duunitori import fetch_search_results

class SearcherAgent:
    def __init__(self, job_boards: List[str] = None, deep: bool = False):
        """
        Searcher Agent orchestrates job search across multiple job boards.

        Args:
            job_boards: list of job board names, e.g., ["duunitori"]
            deep: whether to fetch full job description
        """
        self.job_boards = job_boards or ["duunitori"]
        self.deep = deep

    def search_jobs(self, skill_profile: dict) -> List[Dict]:
        """
        1. Build deterministic queries
        2. Search each job board
        3. Deduplicate results
        4. Optionally save raw JSON
        """
        all_jobs = []

        # 1️⃣ Build queries
        queries = build_queries(skill_profile)

        # 2️⃣ Iterate queries and job boards
        for query in queries:
            for board in self.job_boards:
                if board.lower() == "duunitori":
                    # call your existing scraper
                    jobs = fetch_search_results(query, deep=self.deep)
                else:
                    # placeholder for future boards
                    jobs = []

                all_jobs.extend(jobs)

                # 3️⃣ Save raw results
                self._save_raw_jobs(jobs, board, query)

        # 4️⃣ Deduplicate by URL
        deduped_jobs = self._deduplicate_jobs(all_jobs)

        return deduped_jobs

    # ----------------------------
    # Helper: save raw JSON
    # ----------------------------
    def _save_raw_jobs(self, jobs: List[Dict], board: str, query: str):
        if not jobs:
            return
        safe_query = query.replace(" ", "_").replace("/", "_")
        os.makedirs("data/job_listings", exist_ok=True)
        path = os.path.join("data/job_listings", f"{board}_{safe_query}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)

    # ----------------------------
    # Helper: deduplicate jobs
    # ----------------------------
    def _deduplicate_jobs(self, jobs: List[Dict]) -> List[Dict]:
        seen = set()
        deduped = []
        for job in jobs:
            url = job.get("url")
            if not url:
                continue
            if url not in seen:
                deduped.append(job)
                seen.add(url)
        return deduped
