"""
Searcher Service - Job Board Scraping and Search.

This module contains the SearcherService class, which searches multiple job
boards for relevant job listings based on candidate-generated keywords. The
service supports multiple job boards (Duunitori, Jobly) and can operate in
"deep mode" to fetch full job descriptions.

The service:
1. Searches each job board with each keyword query (job boards scraped in parallel)
2. Saves raw job listings to disk for debugging
3. Deduplicates jobs across queries and boards (by URL)
4. Returns a consolidated list of unique job listings

Performance:
    Job boards are scraped in parallel for each query using ThreadPoolExecutor,
    significantly reducing total scraping time when multiple boards are used.
    Queries are processed sequentially to avoid overwhelming job boards with
    too many concurrent requests.
"""

import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Callable, Any, Tuple

from jobsai.config.paths import RAW_JOB_LISTING_PATH
from jobsai.utils.exceptions import CancellationError
from jobsai.utils.scrapers.duunitori import scrape_duunitori
from jobsai.utils.scrapers.jobly import scrape_jobly
from jobsai.utils.scrapers.indeed import scrape_indeed
from jobsai.utils.logger import get_logger

logger = get_logger(__name__)


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
        Job boards are scraped in parallel for each query to improve performance.
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

        # Search each keyword query sequentially, but parallelize job boards within each query
        # This creates a cartesian product: all boards × all keywords
        # Parallelization: For each query, scrape all boards simultaneously
        for query in keywords:
            # Check for cancellation before processing each query
            if cancellation_check and cancellation_check():
                logger.info(" Job search cancelled by user")
                raise CancellationError("Pipeline cancelled during job search")

            # Scrape all job boards in parallel for this query
            query_results = self._scrape_boards_parallel(
                query, job_boards, deep_mode, cancellation_check
            )

            # Check for cancellation after parallel scraping
            if cancellation_check and cancellation_check():
                logger.info(" Job search cancelled by user")
                raise CancellationError("Pipeline cancelled during job search")

            # Collect all jobs from this query
            for job_board, jobs in query_results:
                all_jobs.extend(jobs)
                self._save_raw_jobs(jobs, job_board, query)

        # Remove duplicate jobs (same URL may appear from multiple queries/boards)
        return self._deduplicate_jobs(all_jobs)

    # ------------------------------
    # Internal functions
    # ------------------------------

    def _scrape_single_board(
        self,
        query: str,
        job_board: str,
        deep_mode: bool,
        cancellation_check: Optional[Callable[[], bool]],
    ) -> Tuple[str, List[Dict]]:
        """Scrape a single job board with a single query.

        Helper function for parallel execution. Returns the job board name
        along with the results for proper result association.

        Args:
            query: Search query string
            job_board: Job board name (e.g., "Duunitori", "Jobly")
            deep_mode: Whether to fetch full job descriptions
            cancellation_check: Optional cancellation check function

        Returns:
            Tuple[str, List[Dict]]: (job_board_name, list_of_jobs)

        Raises:
            CancellationError: If cancellation_check returns True
        """
        logger.info(" Searching %s for query '%s'", job_board, query)

        # Cache lowercase job board name to avoid repeated .lower() calls
        job_board_lower = job_board.lower()

        # Route to appropriate scraper based on job board name
        # Pass cancellation_check to scrapers for checking during long operations
        if job_board_lower == "duunitori":
            jobs = scrape_duunitori(
                query,
                deep_mode=deep_mode,
                cancellation_check=cancellation_check,
            )
        elif job_board_lower == "jobly":
            jobs = scrape_jobly(
                query,
                deep_mode=deep_mode,
                cancellation_check=cancellation_check,
            )
        elif job_board_lower == "indeed":
            jobs = scrape_indeed(
                query,
                deep_mode=deep_mode,
                cancellation_check=cancellation_check,
            )
        else:
            # Unknown job board - skip with empty result
            logger.warning(
                "Unknown job board",
                extra={"extra_fields": {"job_board": job_board, "query": query}},
            )
            jobs = []

        return (job_board, jobs)

    def _scrape_boards_parallel(
        self,
        query: str,
        job_boards: List[str],
        deep_mode: bool,
        cancellation_check: Optional[Callable[[], bool]],
    ) -> List[Tuple[str, List[Dict]]]:
        """Scrape multiple job boards in parallel for a single query.

        Uses ThreadPoolExecutor to scrape all job boards simultaneously,
        significantly reducing total scraping time when multiple boards are used.

        Args:
            query: Search query string
            job_boards: List of job board names to scrape
            deep_mode: Whether to fetch full job descriptions
            cancellation_check: Optional cancellation check function

        Returns:
            List[Tuple[str, List[Dict]]]: List of (job_board_name, list_of_jobs) tuples

        Raises:
            CancellationError: If cancellation_check returns True during execution
        """
        results = []

        # Use ThreadPoolExecutor to scrape all boards in parallel
        # max_workers is set to number of boards (typically 2)
        with ThreadPoolExecutor(max_workers=len(job_boards)) as executor:
            # Submit all scraping tasks
            future_to_board = {
                executor.submit(
                    self._scrape_single_board,
                    query,
                    board,
                    deep_mode,
                    cancellation_check,
                ): board
                for board in job_boards
            }

            # Collect results as they complete
            for future in as_completed(future_to_board):
                # Check for cancellation before processing each completed result
                if cancellation_check and cancellation_check():
                    # Cancel remaining futures
                    for f in future_to_board:
                        f.cancel()
                    logger.info(" Job search cancelled by user")
                    raise CancellationError("Pipeline cancelled during job search")

                try:
                    board_name, jobs = future.result()
                    results.append((board_name, jobs))
                    logger.info(
                        " Completed scraping %s for query '%s': %d jobs found",
                        board_name,
                        query,
                        len(jobs),
                    )
                except CancellationError:
                    # Re-raise cancellation errors
                    for f in future_to_board:
                        f.cancel()
                    raise
                except Exception as e:
                    # Log errors but continue with other boards
                    board_name = future_to_board[future]
                    logger.error(
                        " Error scraping %s for query '%s': %s",
                        board_name,
                        query,
                        str(e),
                        exc_info=True,
                    )
                    # Add empty result to maintain consistency
                    results.append((board_name, []))

        return results

    def _save_raw_jobs(
        self, jobs: List[Dict[str, Any]], board: str, query: str
    ) -> None:
        """Save raw job listings to disk for debugging and record-keeping.

        Persists job listings to JSON files with a structured filename that
        includes timestamp, job board name, and search query. This allows
        for later analysis and debugging of search results.

        Only saves if SAVE_RAW_JOBS environment variable is set to "true".
        This prevents unnecessary I/O in production Lambda environments.

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
        # Check if file saving is enabled (disabled by default in production)
        save_raw_jobs = os.environ.get("SAVE_RAW_JOBS", "false").lower() == "true"
        if not save_raw_jobs:
            return

        if not jobs:
            return

        # Cache lowercase board name to avoid repeated .lower() calls
        board_lower = board.lower()

        # Sanitize query for use in filename
        # Replace spaces and forward slashes with underscores
        safe_query = query.replace(" ", "_").replace("/", "_")

        # Construct filename: timestamp_board_query.json
        filename = f"{self.timestamp}_{board_lower}_{safe_query}.json"
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

        logger.info(
            "Deduplicated jobs",
            extra={
                "extra_fields": {
                    "total_jobs": len(jobs),
                    "unique_jobs": len(deduped),
                    "duplicates_removed": len(jobs) - len(deduped),
                }
            },
        )
        return deduped
