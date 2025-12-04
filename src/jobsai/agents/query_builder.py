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
    ) -> List[str]:
        """Create the keywords.

        Makes an LLM call with the candidate profile to create the keywords.

        Args:
            profile (str): The candidate profile text.

        Returns:
            List[str]: The list of keywords.
        """

        # Build prompt from profile
        USER_PROMPT = USER_PROMPT_BASE.format(profile=profile)

        # Get keywords from LLM (returns a string)
        raw_response = call_llm(SYSTEM_PROMPT, USER_PROMPT)

        # Extract JSON from the response
        json_text = extract_json(raw_response)
        if json_text is None:
            raise ValueError("LLM did not return parseable JSON for keywords.")

        # Parse the JSON dictionary
        keywords_dict = json.loads(json_text)

        # Extract the values from the dictionary into a list
        keywords = list(keywords_dict.values())

        return keywords
