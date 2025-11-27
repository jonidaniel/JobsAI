"""
JobsAI/src/jobsai/agents/profiler.py

Acts as the PROFILER AGENT.

CLASSES:
    ProfilerAgent

FUNCTIONS (in order of workflow):
    1. ProfilerAgent.create_profile   (public use)
    2. ProfilerAgent._merge_profiles  (internal use)
    3. ProfilerAgent._load_profile    (internal use)
    4. ProfilerAgent._save_profile    (internal use)
"""

import os
import logging
import json
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from jobsai.config.schemas import SkillProfile

from jobsai.utils.llms import call_llm, extract_json
from jobsai.utils.normalization import normalize_parsed

logger = logging.getLogger(__name__)


class ProfilerAgent:
    """
    Orchestrate candidate assessment.

    Responsibilities:
    1. Assess the candidate's skills
    2. Form a skill profile of the candidate
    3. Merge the profile with existing profile
    4. Save the profile
    """

    def __init__(self, profile_path: Path, timestamp: str):
        """
        Construct the AssessorAgent class.

        Args:
            model: the OpenAI model
            key: the OpenAI API key
            profile_path: the path to the candidate's skill profile
        """

        self.profile_path = profile_path
        self.timestamp = timestamp

    # ------------------------------
    # Public interface
    # ------------------------------
    def create_profile(self, system_prompt: str, user_prompt: str) -> SkillProfile:
        """
        Create skill profile.

        Make an LLM call, extract JSON from the response,
        parse the JSON, and normalize it.

        Args:
            system_prompt: system prompt for the LLM
            user_prompt: user prompt for the LLM

        Returns:
            profile: the candidate's skill profile
        """

        print()
        logger.info(" CREATING SKILL PROFILE...")

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

    def _merge_profiles(self, new_profile: SkillProfile) -> SkillProfile:
        """
        Merge new_profile into existing profile (e.g. union lists and max experience levels).

        Args:
            new_profile: the new skill profile

        Returns:
            new_profile: the new skill profile
            merged_profile: the merged skill profile
        """
        # Load existing skill profile from /memory/vector_db/skill_profile.json
        existing = self._load_profile()

        # If running for the first time
        if not existing:
            self._save_profile(new_profile)
            return new_profile

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
                    existing.model_dump()[list_key] + new_profile.model_dump()[list_key]
                )
            )

        # Merge experience levels (take max)
        el_existing = existing.experience_level.model_dump(by_alias=True)
        el_new = new_profile.experience_level.model_dump(by_alias=True)
        merged_el = {}
        for k in ["Python", "JavaScript", "Agentic AI", "AI/ML"]:
            merged_el[k] = max(
                int(el_existing.get(k, 0) or 0), int(el_new.get(k, 0) or 0)
            )
        merged["experience_level"] = merged_el
        merged["name"] = new_profile.name or existing.name
        merged_profile = SkillProfile(**merged)

        # Save merged skill profile to /memory/vector_db/skill_profile.json
        self._save_profile(merged_profile)

        return merged_profile

    def _load_profile(self) -> Optional[SkillProfile]:
        """
        Load existing skill profile.

        Returns:
            SkillProfile(**data): the existing skill profile if skill_profile.json is intact
            None: if skill_profile.json is corrupt
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

    def _save_profile(self, profile: SkillProfile):
        """
        Save the skills JSON to the vector database.

        Args:
            profile: the merged skill profile
        """

        out = json.loads(profile.model_dump_json(by_alias=True))

        # Form a dated filename
        filename = f"{self.timestamp}_skill_profile.json"

        # Join the skill profile path and the dated filename
        path = os.path.join(self.profile_path, filename)

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)

            logger.info(
                f" SKILL PROFILE CREATED: Saved to /%s/{filename}\n",
                self.profile_path,
            )
        except Exception as e:
            logger.error(f" SKILL PROFILE CREATION FAILED: {e}\n")
