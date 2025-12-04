"""
Orchestrates the creation of the candidate profile.

CLASSES:
    ProfilerAgent

FUNCTIONS:
    create_profile   (public)
"""

import logging
from typing import Dict

from jobsai.utils.llms import call_llm

from jobsai.config.prompts import (
    PROFILER_SYSTEM_PROMPT as SYSTEM_PROMPT,
    PROFILER_USER_PROMPT as USER_PROMPT_BASE,
)

logger = logging.getLogger(__name__)


class ProfilerAgent:
    """Creates the candidate profile.

    Responsibilities:
        1. Call the LLM with the system prompt and user prompt
        2. Return the raw response
    """

    # ------------------------------
    # Public interface
    # ------------------------------
    def create_profile(
        self,
        form_submissions: Dict,
    ) -> str:
        """Create the candidate profile.

        Args:
            form_submissions (Dict): The user's form submissions from frontend.

        Returns:
            str: The candidate profile.
        """

        USER_PROMPT = USER_PROMPT_BASE.format(form_submissions=form_submissions)

        raw_response = call_llm(SYSTEM_PROMPT, USER_PROMPT)

        return raw_response
