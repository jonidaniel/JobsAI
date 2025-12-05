"""
Builds search queries from candidate profile.

CLASSES:
    QueryBuilderAgent

FUNCTIONS:
    create_keywords   (public)
"""

import logging
import json
from typing import List

from jobsai.config.prompts import (
    QUERY_BUILDER_SYSTEM_PROMPT as SYSTEM_PROMPT,
    QUERY_BUILDER_USER_PROMPT as USER_PROMPT_BASE,
)

from jobsai.utils.llms import call_llm, extract_json

logger = logging.getLogger(__name__)


class QueryBuilderAgent:
    """Builds search queries from the candidate profile.

    Responsibilities:
    1. Call the LLM with the system prompt and the candidate profile text
    2. Return the list of keywords
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

        # Build prompt from profile
        USER_PROMPT = USER_PROMPT_BASE.format(profile=profile)

        for attempt in range(max_retries + 1):
            try:
                # Get keywords from LLM (returns a string)
                raw_response = call_llm(SYSTEM_PROMPT, USER_PROMPT)

                # Extract JSON from the response
                json_text = extract_json(raw_response)
                if json_text is None:
                    if attempt < max_retries:
                        logger.warning(
                            f"LLM did not return parseable JSON (attempt {attempt + 1}/{max_retries + 1}). "
                            "Retrying..."
                        )
                        continue
                    else:
                        logger.error(
                            f"LLM failed to return parseable JSON after {max_retries + 1} attempts. "
                            f"Raw response: {raw_response[:500]}"
                        )
                        raise ValueError(
                            "LLM did not return parseable JSON for keywords after multiple attempts. "
                            "Please try again or check the profile input."
                        )

                # Parse the JSON dictionary
                try:
                    keywords_dict = json.loads(json_text)
                except json.JSONDecodeError as e:
                    if attempt < max_retries:
                        logger.warning(
                            f"JSON parsing failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}. "
                            "Retrying..."
                        )
                        continue
                    else:
                        logger.error(
                            f"JSON parsing failed after {max_retries + 1} attempts: {str(e)}. "
                            f"Extracted JSON text: {json_text[:500]}"
                        )
                        raise ValueError(
                            f"Failed to parse JSON response from LLM: {str(e)}"
                        ) from e

                # Validate that we got a dictionary
                if not isinstance(keywords_dict, dict):
                    if attempt < max_retries:
                        logger.warning(
                            f"LLM returned non-dict JSON (attempt {attempt + 1}/{max_retries + 1}). "
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
                            f"LLM returned empty keywords list (attempt {attempt + 1}/{max_retries + 1}). "
                            "Retrying..."
                        )
                        continue
                    else:
                        raise ValueError("LLM returned an empty keywords list")

                logger.info(f"Successfully extracted {len(keywords)} keywords")
                return keywords

            except ValueError:
                # Re-raise ValueError (these are our validation errors, not retryable)
                raise
            except Exception as e:
                # Unexpected errors - retry if we have attempts left
                if attempt < max_retries:
                    logger.warning(
                        f"Unexpected error creating keywords (attempt {attempt + 1}/{max_retries + 1}): "
                        f"{type(e).__name__}: {str(e)}. Retrying..."
                    )
                    continue
                else:
                    logger.error(
                        f"Failed to create keywords after {max_retries + 1} attempts: "
                        f"{type(e).__name__}: {str(e)}"
                    )
                    raise

        # Should never reach here, but just in case
        raise ValueError("Failed to create keywords after all retry attempts")
