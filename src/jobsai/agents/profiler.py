"""
Profiler Agent - Candidate Profile Generation.

This module contains the ProfilerAgent class, which uses an LLM to extract and
structure candidate skills and experience from form submissions. The agent
transforms raw form data into a comprehensive text profile that describes the
candidate's skills, strengths, and job preferences.

The profile is used throughout the pipeline for:
- Generating search keywords
- Matching jobs to candidate skills
- Writing personalized cover letters
"""

from typing import Dict, Any

from jobsai.utils.llms import call_llm

from jobsai.config.prompts import (
    PROFILER_SYSTEM_PROMPT as SYSTEM_PROMPT,
    PROFILER_USER_PROMPT as USER_PROMPT_BASE,
)


class ProfilerAgent:
    """Agent responsible for creating candidate profiles from form submissions.

    Uses an LLM to analyze form submission data and generate a comprehensive
    text profile describing the candidate's skills, experience levels, and
    professional characteristics.

    The profile is generated as free-form text that captures:
    - Core skills and strengths
    - Experience levels with various technologies
    - Professional characteristics and work style
    - Job preferences and career goals
    - Unique value propositions

    Attributes:
        None (stateless agent - no instance variables required)
    """

    # ------------------------------
    # Public interface
    # ------------------------------
    def create_profile(self, form_submissions: Dict[str, Any]) -> str:
        """Create a comprehensive candidate profile from form submissions.

        Processes the form data (technology experience levels, job preferences,
        personal description) and uses an LLM to generate a structured text
        profile that summarizes the candidate's skills and professional profile.

        The LLM is instructed to extract:
        - Core technical skills and expertise areas
        - Experience levels with specific technologies
        - Professional characteristics and work style
        - Job preferences and career goals
        - Unique strengths and value propositions

        Args:
            form_submissions (Dict): Form data from frontend containing:
                - Technology experience levels (slider values 0-7)
                - Job level preferences (Entry, Intermediate, Expert, Intern)
                - Personal description and additional information
                - Technology categories (languages, databases, frameworks, etc.)

        Returns:
            str: A comprehensive text profile describing the candidate's skills,
                experience, and professional characteristics. This profile is
                used throughout the pipeline for job matching and cover letter
                generation.

        Raises:
            RuntimeError: If LLM call fails after retries (handled by pipeline)
        """
        # Format the user prompt with the form submission data
        USER_PROMPT = USER_PROMPT_BASE.format(form_submissions=form_submissions)

        # Call LLM to generate the profile
        # The LLM analyzes the form data and creates a comprehensive profile
        raw_response = call_llm(SYSTEM_PROMPT, USER_PROMPT)

        return raw_response
