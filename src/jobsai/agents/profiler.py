"""
JobsAI/src/jobsai/agents/profiler.py

Acts as the PROFILER AGENT.

CLASSES:
    ProfilerAgent

FUNCTIONS (in order of workflow):
    1. ProfilerAgent.create_profile   (public use)
    2. ProfilerAgent._build_prompt    (internal use)
    3. ProfilerAgent._merge_profiles  (internal use)
    4. ProfilerAgent._load_profile    (internal use)
    5. ProfilerAgent._save_profile    (internal use)
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
        timestamp (str): The backend-wide timestamp of the moment when the main function was started.
    """

    def __init__(self, timestamp: str):
        self.timestamp = timestamp

    # ------------------------------
    # Public interface
    # ------------------------------
    def create_profile(
        self,
        submits: Dict,
    ) -> SkillProfile:
        """Create the candidate's skill profile.

        Makes an LLM call, extracts JSON from the response, parses the JSON, and normalizes it.

        Args:
            submits (Dict): The user's submits from frontend.

        Returns:
            SkillProfile: The candidate's skill profile.
        """

        print()
        logger.info(" CREATING SKILL PROFILE ...")

        # Build the final user prompt from base user prompt, actual user input, and output schema
        user_prompt = self._build_prompt(submits)

        # Retrieve raw LLM response that contains the skill profile
        raw = call_llm(SYSTEM_PROMPT, user_prompt)

        # Extract the JSON substring from the raw response
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

        # Merge the profile with an existing profile
        merged_profile = self._merge_profiles(skill_profile)

        # return the merged profile
        return merged_profile

    # ------------------------------
    # Internal functions
    # ------------------------------

    def _build_prompt(self, submits: Dict) -> str:
        """Build the final user prompt for an LLM.

        Args:
            submits (Dict): The user's submits from frontend.

        Returns:
            str: The final user prompt for an LLM.
        """

        # Extract general text and build experience lines in a single pass
        user_input = submits.get("general", "")
        experience_lines = []

        for key, value in submits.items():
            # Skip "general" key as it's already handled
            if key == "general":
                continue

            # Map key to proper term (e.g. "javascript" to "JavaScript")
            mapped_key = SUBMIT_ALIAS_MAP.get(key, key)

            # Convert frontend's index-like values (1–7) into actual years
            if value in EXPERIENCE_ALIAS_MAP:
                experience_text = EXPERIENCE_ALIAS_MAP[value]
                experience_lines.append(
                    f"\nI have {experience_text} of experience with {mapped_key}."
                )

        # Combine general input with experience lines
        user_input = user_input + "".join(experience_lines)

        # Insert user input and output schema into the user prompt to create final user prompt
        final_user_prompt = USER_PROMPT.format(
            user_input=user_input, output_schema=OUTPUT_SCHEMA
        )

        print(final_user_prompt)

        return final_user_prompt

    def _merge_profiles(self, skill_profile: SkillProfile) -> SkillProfile:
        """Merge the new skill profile into the existing skill profile.

        Args:
            skill_profile (SkillProfile): The candidate's skill profile.

        Returns:
            SkillProfile: The skill profile unmodified if there is not an existing skill profile, a merged skill profile if there was an existing skill profile.
        """
        # Load existing skill profile from /src/jobsai/memory/vector_db/
        existing = self._load_profile()

        # If running for the first time
        if not existing:
            self._save_profile(skill_profile)
            return skill_profile

        print()
        logger.info(" MERGING SKILL PROFILE WITH EXISTING PROFILE ...")

        # Merge lists
        merged = existing.model_dump()
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
            merged[list_key] = list(
                dict.fromkeys(
                    existing.model_dump()[list_key]
                    + skill_profile.model_dump()[list_key]
                )
            )

        # Merge experience levels (take max)
        el_existing = existing.experience_level.model_dump(by_alias=True)
        el_new = skill_profile.experience_level.model_dump(by_alias=True)
        merged_el = {}
        for k in ["Python", "JavaScript", "Agentic AI", "AI/ML"]:
            merged_el[k] = max(
                int(el_existing.get(k, 0) or 0), int(el_new.get(k, 0) or 0)
            )
        merged["experience_level"] = merged_el
        merged["name"] = skill_profile.name or existing.name
        merged_profile = SkillProfile(**merged)

        # Save merged skill profile to /src/jobsai/memory/vector_db/
        self._save_profile(merged_profile)

        return merged_profile

    def _load_profile(self) -> Optional[SkillProfile]:
        """Load existing skill profile.

        Returns:
            SkillProfile or None: A new `SkillProfile`instance if skill_profile.json is intact, None if skill_profile is corrupt.
        """

        # TURHA?
        if not SKILL_PROFILE_PATH.exists():
            return None

        # Get the latest skill profile from /src/jobsai/memory/vector_db/
        skill_profiles = sorted(os.listdir(SKILL_PROFILE_PATH))
        latest_skill_profile = skill_profiles[-1] if skill_profiles else None

        # If not running for the first time
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
                f" SKILL PROFILE SAVED TO /%s/{filename}\n",
                SKILL_PROFILE_PATH,
            )
        except Exception as e:
            logger.error(f" SKILL PROFILE FAILED: {e}\n")
