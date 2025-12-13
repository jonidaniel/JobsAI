"""
Searcher Service - Job Board Scraping and Search.

This module contains the SearcherService class, which searches multiple job
boards for relevant job listings based on candidate-generated keywords. The
service supports multiple job boards (Duunitori, Jobly) and can operate in
"deep mode" to fetch full job descriptions.

The service:
1. Searches each job board with each keyword query
2. Saves raw job listings to disk for debugging
3. Deduplicates jobs across queries and boards (by URL)
4. Returns a consolidated list of unique job listings
"""

import os
import logging
import json
from typing import List, Dict, Optional, Callable, Any

from jobsai.config.paths import RAW_JOB_LISTING_PATH
from jobsai.utils.exceptions import CancellationError

from jobsai.utils.scrapers.duunitori import scrape_duunitori
from jobsai.utils.scrapers.jobly import scrape_jobly

logger = logging.getLogger(__name__)


class SearcherService:
    """Service responsible for searching job boards and collecting job listings.

    Searches multiple job boards using candidate-generated keywords to find
    relevant job postings. Supports multiple job boards and can fetch full
    job descriptions in "deep mode" for better matching accuracy.

    The service handles:
    - Multi-board searching (Duunitori, Jobly, and extensible to others)
    - Multiple keyword queries per board
    - Deduplication of jobs across queries and boards
    - Persistence of raw job listings for debugging

    Args:
        timestamp (str): Backend-wide timestamp for consistent file naming.
            Format: YYYYMMDD_HHMMSS (e.g., "20250115_143022")
    """

    def __init__(self, timestamp: str) -> None:
        self.timestamp: str = timestamp

    # ------------------------------
    # Public interface
    # ------------------------------
    def search_jobs(
        self,
        keywords: List[str],
        job_boards: List[str],
        deep_mode: bool,
        cancellation_check=None,
    ) -> List[Dict]:
        """Search all specified job boards using candidate-generated keywords.

        Executes searches across multiple job boards with each keyword query.
        Each search result is saved to disk for debugging, and all results are
        deduplicated before returning.

        Args:
            keywords (List[str]): List of search keywords generated from
                candidate profile (e.g., ["ai engineer", "software engineer"]).
                Typically 10 keywords per candidate.
            job_boards (List[str]): List of job board names to search.
                Supported: "Duunitori", "Jobly" (case-insensitive).
            deep_mode (bool): If True, fetches full job descriptions for each
                listing. If False, only fetches description snippets.
                Deep mode provides better matching accuracy but is slower.
            cancellation_check (Optional[Callable[[], bool]]): Optional callable
                that returns True if the operation should be cancelled. Checked
                before processing each query and job board.

        Returns:
            List[Dict]: Deduplicated list of job listings. Each job dict contains:
                - "title": Job title
                - "company": Company name
                - "location": Job location
                - "url": Job posting URL
                - "description_snippet": Short description (always present)
                - "full_description": Full description (only if deep_mode=True)

        Raises:
            CancellationError: If cancellation_check returns True during execution
        """
        all_jobs = []

        # Search each job board with each keyword query
        # This creates a cartesian product: all boards × all keywords
        for query in keywords:
            # Check for cancellation before processing each query
            if cancellation_check and cancellation_check():
                logger.info(" Job search cancelled by user")
                raise CancellationError("Pipeline cancelled during job search")

            for job_board in job_boards:
                # Check for cancellation before processing each job board
                if cancellation_check and cancellation_check():
                    logger.info(" Job search cancelled by user")
                    raise CancellationError("Pipeline cancelled during job search")

                logger.info(" Searching %s for query '%s'", job_board, query)

                # Route to appropriate scraper based on job board name
                # Pass cancellation_check to scrapers for checking during long operations
                if job_board.lower() == "duunitori":
                    jobs = scrape_duunitori(
                        query,
                        deep_mode=deep_mode,
                        cancellation_check=cancellation_check,
                    )
                elif job_board.lower() == "jobly":
                    jobs = scrape_jobly(
                        query,
                        deep_mode=deep_mode,
                        cancellation_check=cancellation_check,
                    )
                else:
                    # Unknown job board - skip with empty result
                    logger.warning(f" Unknown job board: {job_board}. Skipping.")
                    jobs = []

                # Check for cancellation after scraping (before saving)
                if cancellation_check and cancellation_check():
                    logger.info(" Job search cancelled by user")
                    raise CancellationError("Pipeline cancelled during job search")

                # Collect jobs and save to disk for debugging
                all_jobs.extend(jobs)
                self._save_raw_jobs(jobs, job_board, query)

        # Remove duplicate jobs (same URL may appear from multiple queries/boards)
        return self._deduplicate_jobs(all_jobs)

    # ------------------------------
    # Internal functions
    # ------------------------------

    def _save_raw_jobs(
        self, jobs: List[Dict[str, Any]], board: str, query: str
    ) -> None:
        """Save raw job listings to disk for debugging and record-keeping.

        Persists job listings to JSON files with a structured filename that
        includes timestamp, job board name, and search query. This allows
        for later analysis and debugging of search results.

        Args:
            jobs (List[Dict]): Job listings to save. Empty list is handled
                gracefully (no file created).
            board (str): Job board name (e.g., "Duunitori", "Jobly").
                Used in filename and converted to lowercase.
            query (str): Search query used to find these jobs.
                Spaces and slashes are replaced with underscores for filename safety.

        File location:
            {RAW_JOB_LISTING_PATH}/{timestamp}_{board}_{query}.json
        """
        if not jobs:
            return

        # Sanitize query for use in filename
        # Replace spaces and forward slashes with underscores
        safe_query = query.replace(" ", "_").replace("/", "_")

        # Construct filename: timestamp_board_query.json
        filename = f"{self.timestamp}_{board.lower()}_{safe_query}.json"
        path = os.path.join(RAW_JOB_LISTING_PATH, filename)

        # Save jobs as pretty-printed JSON
        with open(path, "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)

        logger.info(" Saved %d raw jobs to %s", len(jobs), path)

    def _deduplicate_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate job listings based on URL.

        Since the same job may appear in multiple search results (different
        queries, different boards), this method deduplicates by URL to ensure
        each unique job appears only once in the final list.

        Args:
            jobs (List[Dict]): List of job listings that may contain duplicates.
                Each job dict must have a "url" key for deduplication.

        Returns:
            List[Dict]: Deduplicated list of jobs, preserving first occurrence
                of each unique URL. Jobs without URLs are excluded.
        """
        seen_urls = set()
        deduped = []

        for job in jobs:
            url = job.get("url")
            # Only include jobs with valid URLs that we haven't seen before
            if url and url not in seen_urls:
                deduped.append(job)
                seen_urls.add(url)

        logger.info(f" Deduplicated {len(jobs)} jobs to {len(deduped)} unique listings")
        return deduped
