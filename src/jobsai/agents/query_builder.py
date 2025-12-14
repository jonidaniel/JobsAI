"""
Query Builder Agent - Search Keyword Generation.

This module contains the QueryBuilderAgent class, which generates job search
keywords from candidate profiles. The agent uses an LLM to analyze the profile
and create a set of optimized search queries that will be used to find relevant
job listings on job boards.

The generated keywords are typically two-word phrases (e.g., "ai engineer",
"software engineer") that are tailored to the candidate's skills and experience.
"""

import json
from typing import List, Dict, Any

from jobsai.config.prompts import (
    QUERY_BUILDER_SYSTEM_PROMPT as SYSTEM_PROMPT,
    QUERY_BUILDER_USER_PROMPT as USER_PROMPT_BASE,
)

from jobsai.utils.llms import call_llm, extract_json
from jobsai.utils.logger import get_logger

logger = get_logger(__name__)


class QueryBuilderAgent:
    """Agent responsible for generating job search keywords from candidate profiles.

    Analyzes a candidate profile and generates a list of optimized search queries
    that will be used to search job boards. The keywords are tailored to the
    candidate's specific skills and experience level.

    The agent includes retry logic to handle cases where the LLM doesn't return
    valid JSON, ensuring robust operation even when the LLM response format varies.

    Attributes:
        None (stateless agent - no instance variables required)
    """

    # ------------------------------
    # Public interface
    # ------------------------------
    def create_keywords(
        self,
        profile: str,
        max_retries: int = 2,
    ) -> List[str]:
        """Create the keywords.

        Makes an LLM call with the candidate profile to create the keywords.
        Includes retry logic if JSON parsing fails.

        Args:
            profile (str): The candidate profile text.
            max_retries (int): Maximum number of retries if JSON parsing fails (default: 2)

        Returns:
            List[str]: The list of keywords.

        Raises:
            ValueError: If LLM consistently fails to return parseable JSON after retries
        """

        # Format the user prompt with the candidate profile
        USER_PROMPT = USER_PROMPT_BASE.format(profile=profile)

        # Retry loop: attempt to get valid JSON response from LLM
        for attempt in range(max_retries + 1):
            try:
                # Call LLM to generate keywords
                # The LLM is instructed to return a dictionary of 10 search queries
                raw_response = call_llm(SYSTEM_PROMPT, USER_PROMPT)

                # Extract JSON from the LLM response
                # LLMs often wrap JSON in markdown code blocks or add extra text
                json_text = extract_json(raw_response)
                if json_text is None:
                    if attempt < max_retries:
                        logger.warning(
                            f" LLM did not return parseable JSON (attempt {attempt + 1}/{max_retries + 1}). "
                            "Retrying..."
                        )
                        continue
                    else:
                        logger.error(
                            f" LLM failed to return parseable JSON after {max_retries + 1} attempts. "
                            f"Raw response: {raw_response[:500]}"
                        )
                        raise ValueError(
                            "LLM did not return parseable JSON for keywords after multiple attempts. "
                            "Please try again or check the profile input."
                        )

                # Parse the JSON dictionary
                try:
                    keywords_dict: Dict[str, str] = json.loads(json_text)
                except json.JSONDecodeError as e:
                    if attempt < max_retries:
                        logger.warning(
                            f" JSON parsing failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}. "
                            "Retrying..."
                        )
                        continue
                    else:
                        logger.error(
                            f" JSON parsing failed after {max_retries + 1} attempts: {str(e)}. "
                            f"Extracted JSON text: {json_text[:500]}"
                        )
                        raise ValueError(
                            f"Failed to parse JSON response from LLM: {str(e)}"
                        ) from e

                # Validate that we got a dictionary
                if not isinstance(keywords_dict, dict):
                    if attempt < max_retries:
                        logger.warning(
                            f" LLM returned non-dict JSON (attempt {attempt + 1}/{max_retries + 1}). "
                            "Retrying..."
                        )
                        continue
                    else:
                        raise ValueError(
                            f"LLM returned JSON but it's not a dictionary. Got: {type(keywords_dict).__name__}"
                        )

                # Extract the values from the dictionary into a list
                keywords = list(keywords_dict.values())

                # Validate we got some keywords
                if not keywords:
                    if attempt < max_retries:
                        logger.warning(
                            f" LLM returned empty keywords list (attempt {attempt + 1}/{max_retries + 1}). "
                            "Retrying..."
                        )
                        continue
                    else:
                        raise ValueError("LLM returned an empty keywords list")

                logger.info(
                    "Successfully extracted keywords",
                    extra={"extra_fields": {"keywords_count": len(keywords)}},
                )
                return keywords

            except ValueError:
                # Re-raise ValueError (these are our validation errors, not retryable)
                raise
            except Exception as e:
                # Unexpected errors - retry if we have attempts left
                if attempt < max_retries:
                    logger.warning(
                        f" Unexpected error creating keywords (attempt {attempt + 1}/{max_retries + 1}): "
                        f"{type(e).__name__}: {str(e)}. Retrying..."
                    )
                    continue
                else:
                    logger.error(
                        f" Failed to create keywords after {max_retries + 1} attempts: "
                        f"{type(e).__name__}: {str(e)}"
                    )
                    raise

        # Should never reach here, but just in case
        raise ValueError("Failed to create keywords after all retry attempts")
