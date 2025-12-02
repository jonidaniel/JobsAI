"""
Orchestrates candidate profiling.

CLASSES:
    ProfilerAgent

FUNCTIONS (in order of workflow):
    1. create_profile   (public use)
    2. _build_prompt    (internal use)
    3. _merge_profiles  (internal use)
    4. _load_profile    (internal use)
    5. _save_profile    (internal use)
"""

import os
import logging
import json
from typing import Dict, Optional

from pydantic import ValidationError

from jobsai.config.paths import SKILL_PROFILE_PATH
from jobsai.config.prompts import (
    PROFILER_SYSTEM_PROMPT as SYSTEM_PROMPT,
    PROFILER_USER_PROMPT as USER_PROMPT,
)
from jobsai.config.schemas import (
    SkillProfile,
    OUTPUT_SCHEMA,
    EXPERIENCE_ALIAS_MAP,
    SUBMIT_ALIAS_MAP,
)

from jobsai.utils.llms import call_llm, extract_json
from jobsai.utils.normalization import normalize_parsed

logger = logging.getLogger(__name__)


class ProfilerAgent:
    """Orchestrates candidate profiling.

    Responsibilities:
    1. Assess the candidate's skills
    2. Form a skill profile of the candidate
    3. Merge the profile with existing profile
    4. Save the profile

    Args:
        timestamp (str): The backend-wide timestamp for consistent file naming.
    """

    def __init__(self, timestamp: str):
        self.timestamp = timestamp

    # ------------------------------
    # Public interface
    # ------------------------------
    def create_profile(
        self,
        form_submissions: Dict,
    ) -> SkillProfile:
        """Create the candidate's skill profile.

        Makes an LLM call, extracts JSON from the response, parses the JSON, and normalizes it.

        Args:
            form_submissions (Dict): The user's form submissions from frontend.

        Returns:
            SkillProfile: The candidate's skill profile.
        """

        # Build the final user prompt
        user_prompt = self._build_prompt(form_submissions)

        # Retrieve raw LLM response
        raw = call_llm(SYSTEM_PROMPT, user_prompt)

        # Extract the JSON from the raw response
        json_text = extract_json(raw)

        if json_text is None:
            raise ValueError("LLM did not return parseable JSON.")

        parsed = json.loads(json_text)
        # Normalize lists and keys
        parsed = normalize_parsed(parsed)

        # Validate with Pydantic
        try:
            skill_profile = SkillProfile(**parsed)
        except ValidationError as e:
            logger.error(" Validation error: %s", e)
            raise

        # Merge the profile with an existing one
        merged_profile = self._merge_profiles(skill_profile)

        return merged_profile

    # ------------------------------
    # Internal functions
    # ------------------------------

    def _build_prompt(self, form_submissions: Dict) -> str:
        """
        Build the final user prompt for the LLM by combining form data.

        Transforms frontend form submissions into a natural language prompt:
        - Extracts "additional-info" (personal description) as the main user input
        - Processes technology sets (languages, databases, etc.) to build experience statements
        - Converts slider values (0-7) to experience descriptions
        - Maps technology keys to proper names (e.g., "javascript" -> "JavaScript")
        - Includes custom text fields (e.g., "text-field1") as additional context
        - Combines everything into a coherent text for the LLM

        Args:
            form_submissions (Dict): The user's form submissions from frontend containing:
                - "general": Array of general question items (not used for prompt building)
                - "additional-info": Array with personal description
                - Technology sets (e.g., "languages", "databases"): Arrays of single-key dicts
                  where keys are technology names (with numeric values 0-7) or "text-field*" (with string values)

        Returns:
            str: The formatted user prompt.
        """

        # Extract personal description from "additional-info"
        # Structure: {"additional-info": [{"additional-info": "Personal description..."}]}
        user_input_parts = []

        additional_info = form_submissions.get("additional-info")
        if (
            additional_info
            and isinstance(additional_info, list)
            and len(additional_info) > 0
        ):
            description = additional_info[0].get("additional-info", "")
            if description and description.strip():
                user_input_parts.append(description.strip())

        # If no description provided, use a default message
        if not user_input_parts:
            user_input_parts.append(
                "I am a software developer looking for new opportunities."
            )

        experience_lines = []
        additional_context_lines = []

        # Process technology sets (languages, databases, web-frameworks, etc.)
        # Structure: {"languages": [{"javascript": 5}, {"python": 3}, {"text-field1": "Custom tech..."}]}
        for question_set_name, items in form_submissions.items():
            # Skip "general" and "additional-info" as they're handled separately
            if question_set_name in ("general", "additional-info"):
                continue

            # Skip if not a list (shouldn't happen, but defensive)
            if not isinstance(items, list):
                continue

            # Process each item in the technology set
            for item in items:
                if not isinstance(item, dict):
                    continue

                # Each item is a single-key dictionary
                for key, value in item.items():
                    # Handle technology keys with numeric experience values (0-7)
                    if isinstance(value, (int, float)) and 0 <= value <= 7:
                        # Map frontend key to proper technology name
                        # e.g., "javascript" -> "JavaScript", "html-css" -> "HTML/CSS"
                        mapped_key = SUBMIT_ALIAS_MAP.get(key, key.title())

                        # Convert numeric slider values (0-7) into natural language
                        # e.g., 1 -> "less than half a year", 7 -> "over 3 years"
                        if value in EXPERIENCE_ALIAS_MAP:
                            experience_text = EXPERIENCE_ALIAS_MAP[value]
                            experience_lines.append(
                                f"I have {experience_text} of experience with {mapped_key}."
                            )

                    # Handle custom text fields (e.g., "text-field1", "text-field1-2")
                    elif isinstance(value, str) and key.startswith("text-field"):
                        if value.strip():
                            additional_context_lines.append(value.strip())

        # Combine all parts into final user input
        # Start with personal description
        user_input = user_input_parts[0]

        # Add experience statements
        if experience_lines:
            user_input += "\n\n" + "\n".join(experience_lines)

        # Add additional context from custom text fields
        if additional_context_lines:
            user_input += "\n\n" + "\n".join(additional_context_lines)

        # Insert user input and output schema into the base user prompt template
        # The LLM will use this to extract structured skill profile
        final_user_prompt = USER_PROMPT.format(
            user_input=user_input, output_schema=OUTPUT_SCHEMA
        )

        print("FINAL_USER_PROMPT_START")
        print(final_user_prompt)
        print("FINAL_USER_PROMPT_END")

        return final_user_prompt

    def _load_profile(self) -> Optional[SkillProfile]:
        """Load the existing skill profile.

        Returns:
            SkillProfile or None:
                - A new `SkillProfile` instance if skill_profile.json is valid.
                - None if skill_profile.json is corrupt.
        """

        if not SKILL_PROFILE_PATH.exists():
            return None

        # Get the latest skill profile from the vector database
        skill_profiles = sorted(os.listdir(SKILL_PROFILE_PATH))
        latest_skill_profile = skill_profiles[-1] if skill_profiles else None

        # If running for the first time, return None
        if latest_skill_profile:
            path = os.path.join(SKILL_PROFILE_PATH, latest_skill_profile)

            with open(path, "r", encoding="utf-8") as f:
                try:
                    # Read the JSON file and turn it into a dictionary
                    data = json.load(f)
                    return SkillProfile(**data)
                except:
                    return None

        return None

    def _save_profile(self, skill_profile: SkillProfile):
        """Save the candidate's skill profile to the vector database.

        Args:
            skill_profile (SkillProfile): The candidate's skill profile (merged or unmodified).
        """

        # ???
        out = json.loads(skill_profile.model_dump_json(by_alias=True))

        # Form a dated filename and make a path
        filename = f"{self.timestamp}_skill_profile.json"
        path = os.path.join(SKILL_PROFILE_PATH, filename)

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)

            logger.info(
                f" Saved skill profile to /%s/{filename}\n",
                SKILL_PROFILE_PATH,
            )
        except Exception as e:
            logger.error(f" Skill profile failed: {e}\n")

    def _merge_profiles(self, skill_profile: SkillProfile) -> SkillProfile:
        """
        Merge the new skill profile with an existing profile (if one exists).

        Merging strategy:
        - Lists: Combine and deduplicate (union of all skills)
        - Experience levels: Take maximum value (highest experience wins)
        - Name: Use new name if provided, otherwise keep existing

        This allows the profile to grow over time as the candidate submits
        additional information through multiple form submissions.

        Args:
            skill_profile (SkillProfile): The newly created skill profile from current submission

        Returns:
            SkillProfile:
                - The new profile unchanged if no existing profile exists
                - A merged profile combining new and existing data if profile exists
        """
        # Load existing skill profile from /src/jobsai/memory/vector_db/
        # Returns None if no profile exists (first time running)
        existing = self._load_profile()

        # If running for the first time, just save and return the new profile
        if not existing:
            self._save_profile(skill_profile)
            return skill_profile

        print()
        logger.info(" MERGING SKILL PROFILE WITH EXISTING PROFILE ...")

        # Start with existing profile as base
        merged_profile_dict = existing.model_dump()

        # Merge list fields: combine lists and remove duplicates
        # Uses dict.fromkeys() trick to preserve order while deduplicating
        for list_key in [
            "core_languages",
            "frameworks_and_libraries",
            "tools_and_platforms",
            "agentic_ai_experience",
            "ai_ml_experience",
            "soft_skills",
            "projects_mentioned",
            "job_search_keywords",
        ]:
            merged_profile_dict[list_key] = list(
                dict.fromkeys(
                    existing.model_dump()[list_key]
                    + skill_profile.model_dump()[list_key]
                )
            )

        # Merge experience levels: take the maximum value
        # This ensures we keep the highest experience level if candidate
        # has provided different values in different submissions
        existing_experience_levels = existing.experience_level.model_dump(by_alias=True)
        new_experience_levels = skill_profile.experience_level.model_dump(by_alias=True)
        merged_experience_levels = {}
        for technology_name in ["Python", "JavaScript", "Agentic AI", "AI/ML"]:
            merged_experience_levels[technology_name] = max(
                int(existing_experience_levels.get(technology_name, 0) or 0),
                int(new_experience_levels.get(technology_name, 0) or 0),
            )
        merged_profile_dict["experience_level"] = merged_experience_levels

        # Use new name if provided, otherwise keep existing name
        merged_profile_dict["name"] = skill_profile.name or existing.name

        # Create merged profile object and validate
        merged_profile = SkillProfile(**merged_profile_dict)

        # Save merged skill profile to /src/jobsai/memory/vector_db/
        self._save_profile(merged_profile)

        return merged_profile
