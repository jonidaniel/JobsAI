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
from pathlib import Path
from typing import Dict, Optional

from pydantic import ValidationError

from jobsai.config.prompts import USER_PROMPT_BASE
from jobsai.config.schemas import SkillProfile, OUTPUT_SCHEMA, SUBMITS_MAP

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
        profile_path (Path): The path to the candidate's skill profile.
        timestamp (str): The backend-wide timestamp of the moment when the main function was started.
    """

    def __init__(self, profile_path: Path, timestamp: str):
        self.profile_path = profile_path
        self.timestamp = timestamp

    # ------------------------------
    # Public interface
    # ------------------------------
    def create_profile(
        self,
        system_prompt: str,
        user_input: str,
        submits: Dict,
    ) -> SkillProfile:
        """Create the candidate's skill profile.

        Makes an LLM call, extracts JSON from the response, parses the JSON, and normalizes it.

        Args:
            system_prompt (str): System prompt for the LLM.
            user_prompt (str): User prompt for the LLM.
            submits (Dict): The user's submits from frontend.

        Returns:
            SkillProfile: The candidate's skill profile.
        """

        print()
        logger.info(" CREATING SKILL PROFILE ...")

        # Build the final user prompt from base user prompt, actual user input, and output schema
        user_prompt = self._build_prompt(user_input, submits)

        # Retrieve raw LLM response that contains the skill profile
        raw = call_llm(system_prompt, user_prompt)

        # Extract the JSON substring from the raw response
        json_text = extract_json(raw)

        if json_text is None:
            raise ValueError("LLM did not return parseable JSON.")

        parsed = json.loads(json_text)
        # Normalize lists and keys
        parsed = normalize_parsed(parsed)
        # Validate with Pydantic
        try:
            profile = SkillProfile(**parsed)
        except ValidationError as e:
            logger.error(" Validation error: %s", e)
            raise

        # Merge the profile with an existing profile
        merged_profile = self._merge_profiles(profile)

        # return the merged profile
        return merged_profile

    # ------------------------------
    # Internal functions
    # ------------------------------

    def _build_prompt(self, user_input: str, submits: Dict) -> str:
        """Build the final user prompt for an LLM.

        Args:
            user_input (str): The user input from frontend payload.
            submits (Dict): The user's submits from frontend.

        Returns:
            str: The final user prompt for an LLM.
        """

        # Iterate over the frontend payload
        for key, value in submits.items():
            # Map key to proper term (e.g. "javascript to "JavaScript")
            for item, mapped in SUBMITS_MAP.items():
                if item == key:
                    key = mapped
            # Convert frontend's index-like values (1–7) into actual years
            if value == 1:
                value = "less than half a year"
            if value == 2:
                value = "less than a year"
            if value == 3:
                value = "less than 1.5 years"
            if value == 4:
                value = "less than 2 years"
            if value == 5:
                value = "less than 2.5 years"
            if value == 6:
                value = "less than 3 years"
            if value == 7:
                value = "over 3 years"

            # Append experience line to user input
            experience = f"\nI have {value} of experience with {key}."
            user_input = user_input + experience

        # Insert user input and output schema into the user prompt base to create final user prompt
        final_user_prompt = USER_PROMPT_BASE.format(
            user_input_placeholder=user_input, output_schema=OUTPUT_SCHEMA
        )

        return final_user_prompt

    def _merge_profiles(self, skill_profile: SkillProfile) -> SkillProfile:
        """Merge the new skill profile into the existing skill profile.

        Args:
            skill_profile (SkillProfile): The candidate's skill profile.

        Returns:
            SkillProfile: The skill profile unmodified if there is not an existing skill profile, a merged skill profile if there was an existing skill profile.
        """
        # Load existing skill profile from /memory/vector_db/skill_profile.json
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

        # Save merged skill profile to src/jobsai/memory/vector_db/
        self._save_profile(merged_profile)

        return merged_profile

    def _load_profile(self) -> Optional[SkillProfile]:
        """Load existing skill profile.

        Returns:
            SkillProfile or None: A new `SkillProfile`instance if skill_profile.json is intact, None if skill_profile is corrupt.
        """

        # TURHA?
        if not self.profile_path.exists():
            return None

        # Get the latest skill profile from /memory/vector_db/
        skill_profiles = sorted(os.listdir(self.profile_path))
        latest_skill_profile = skill_profiles[-1] if skill_profiles else None

        # If not running for the first time
        if latest_skill_profile:
            path = os.path.join(self.profile_path, latest_skill_profile)

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

        logger.info(" SAVING SKILL PROFILE ...")

        # ???
        out = json.loads(skill_profile.model_dump_json(by_alias=True))

        # Form a dated filename and make a path
        filename = f"{self.timestamp}_skill_profile.json"
        path = os.path.join(self.profile_path, filename)

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)

            logger.info(
                f" SKILL PROFILE SAVED: /%s/{filename}\n",
                self.profile_path,
            )
        except Exception as e:
            logger.error(f" SKILL PROFILE CREATION FAILED: {e}\n")
