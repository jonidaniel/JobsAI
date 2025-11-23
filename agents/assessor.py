# ---------- ASSESSOR AGENT ----------

import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional

from pydantic import ValidationError

from openai import OpenAI

from utils import normalize_list

from config.schemas import SkillProfile

logger = logging.getLogger(__name__)

class AssessorAgent:
    """
    AssessorAgent class orchestrates candidate assessment.

    Responsibilities:
    1. Assess the candidate's skills
    2. Form a skill profile of the candidate
    3. Merge the profile with existing profile
    4. Save the profile
    """

    def __init__(self, model: str, key: str, profile_path: Path):
        """
        Construct the AssessorAgent class.

        Args:
            model: the OpenAI model
            key: the OpenAI API key
            profile_path: the path to the candidate's skill profile
        """

        self.model = model
        self.key = key
        self.profile_path = profile_path

    # ------------------------------
    # Public interface
    # ------------------------------
    def assess(self, prompt: str, system_prompt: str) -> SkillProfile:
        """
        Assess the candidate's skills.

        Make an LLM call, extract JSON from the response,
        parse the JSON, and normalize it.

        Args:
            prompt: the complete user prompt for the LLM
            system_prompt: the system prompt for the LLM

        Returns:
            profile: the candidate's skill profile
        """

        # Retrieve the raw LLM response
        raw = self._call_llm(prompt, system_prompt)

        # Extract the JSON substring from the raw response
        json_text = self._extract_json(raw)

        if json_text is None:
            raise ValueError("LLM did not return parseable JSON.")

        parsed = json.loads(json_text)
        # Normalize lists and keys
        parsed = self._normalize_parsed(parsed)
        # Validate with Pydantic
        try:
            profile = SkillProfile(**parsed)
        except ValidationError as e:
            logger.error(" Validation error: %s", e)
            raise

        # Merge the profile with an existing profile
        merged_profile = self.merge_update(profile)

        print()
        logger.info(" SKILL ASSESSMENT COMPLETED\n")

        # return the merged profile
        return merged_profile

    # ------------------------------
    # Internal functions
    # ------------------------------

    def _call_llm(self, prompt: str, system_prompt: str, max_tokens: int = 800) -> str:
        """
        Call an LLM with the user prompt.

        Args:
            prompt: complete user prompt for the LLM
            system_prompt: system prompt for the LLM
            max_tokens: the maximum amount of tokens reserved for the LLM call

        Returns:
            text: the complete LLM response text
        """

        if not self.model:
            logger.warning(" OPENAI_MODEL not found in environment. OpenAI calls will fail without it.")
        if not self.key:
            logger.warning(" OPENAI_API_KEY not found in environment. OpenAI calls will fail without it.")
        client = OpenAI()
        client.api_key = self.key
        if not client.api_key:
            raise RuntimeError("OpenAI API key not configured. Set OPENAI_API_KEY env var.")

        print()
        logger.info(" SKILL ASSESSMENT STARTING...\n")

        # Get response from LLM
        response = client.chat.completions.create(
            model=self.model,
            messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.2,
        )

        text = response.choices[0].message.content
        logger.debug(" LLM response: %s", text[:500])

        return text

    def _extract_json(self, text: str) -> Optional[str]:
        """
        Extract the JSON substring from the raw LLM response.

        Args:
            text: the raw LLM response

        Returns:
            text: the extracted JSON
            None: if JSON cannot be extracted from the response
        """

        # Find where the JSON starts
        start = text.find("{")

        # If a brace isn't present
        if start == -1:
            return None

        # Attempt to balance braces
        brace = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                brace += 1
            elif text[i] == "}":
                brace -= 1
                if brace == 0:
                    return text[start:i+1]
        # Fallback: try direct load
        try:
            json.loads(text)
            return text
        except Exception:
            return None

    def _normalize_parsed(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize the parsed JSON.

        Args:
            parsed: parsed skills JSON

        Returns:
            parsed: the normalized parsed skills JSON
        """

        keys = [
            "name", "core_languages", "frameworks_and_libraries", "tools_and_platforms",
            "agentic_ai_experience", "ai_ml_experience", "soft_skills", "projects_mentioned",
            "experience_level", "job_search_keywords"
        ]
        # Ensure all keys exist in the JSON the LLM generated
        for k in keys:
            if k not in parsed:
                parsed[k] = [] if k != "experience_level" else {"Python": 0, "JavaScript": 0, "Agentic AI": 0, "AI/ML": 0}

        # Normalize lists
        for list_key in ["core_languages", "frameworks_and_libraries", "tools_and_platforms",
                         "agentic_ai_experience", "ai_ml_experience", "soft_skills", "projects_mentioned", "job_search_keywords"]:
            if isinstance(parsed.get(list_key), list):
                parsed[list_key] = normalize_list(parsed[list_key])
            else:
                parsed[list_key] = []

        # Normalize experience_level keys and values
        el = parsed.get("experience_level", {})
        norm_el = {
            "Python": int(el.get("Python") or 0),
            "JavaScript": int(el.get("JavaScript") or 0),
            "Agentic AI": int(el.get("Agentic AI") or el.get("Agentic_Ai") or 0),
            "AI/ML": int(el.get("AI/ML") or el.get("AI_ML") or 0)
        }
        parsed["experience_level"] = norm_el

        # Name normalization
        if not parsed.get("name") or not isinstance(parsed["name"], str):
            parsed["name"] = ""
        else:
            parsed["name"] = parsed["name"].strip()
        return parsed

    def merge_update(self, new_profile: SkillProfile) -> SkillProfile:
        """
        Merge new_profile into existing profile (e.g. union lists and max experience levels).

        Args:
            new_profile: the new skill profile

        Returns:
            new_profile: the new skill profile
            merged_profile: the merged skill profile
        """
        # Load existing skill profile from /memory/vector_db/skill_profile.json
        existing = self.load_existing()

        if not existing:
            self.save(new_profile)
            return new_profile

        # Merge lists
        merged = existing.model_dump()
        for list_key in ["core_languages", "frameworks_and_libraries", "tools_and_platforms",
                         "agentic_ai_experience", "ai_ml_experience", "soft_skills", "projects_mentioned", "job_search_keywords"]:
            merged[list_key] = list(dict.fromkeys(existing.model_dump()[list_key] + new_profile.model_dump()[list_key]))

        # Merge experience levels (take max)
        el_existing = existing.experience_level.model_dump(by_alias=True)
        el_new = new_profile.experience_level.model_dump(by_alias=True)
        merged_el = {}
        for k in ["Python", "JavaScript", "Agentic AI", "AI/ML"]:
            merged_el[k] = max(int(el_existing.get(k, 0) or 0), int(el_new.get(k, 0) or 0))
        merged["experience_level"] = merged_el
        merged["name"] = new_profile.name or existing.name
        merged_profile = SkillProfile(**merged)

        # Save merged skill profile to /memory/vector_db/skill_profile.json
        self.save(merged_profile)

        return merged_profile

    def save(self, profile: SkillProfile):
        """
        Save the skills JSON to the vector database.

        Args:
            profile: the merged skill profile
        """

        # Write JSON to /memory/vector_db/skill_profile.json
        # Convert a JSON-formatted string into a Python object (dict, list, etc.).
        out = json.loads(profile.model_dump_json(by_alias=True))

        # Open /memory/vector_db/skill_profile.json
        with open(self.profile_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

        logger.info(" Saved skill profile to %s", self.profile_path)

    def load_existing(self) -> Optional[SkillProfile]:
        """
        Load existing SkillProfile.

        Returns:
            SkillProfile(**data): the existing skill profile if skill_profile.json is intact
            None: if skill_profile.json is corrupt
        """

        if not self.profile_path.exists():
            return None

        # Open memory/vector_db/skill_profile.json
        with open(self.profile_path, "r", encoding="utf-8") as f:
            try:
                # Read the JSON file and turn it into a dictionary
                data = json.load(f)
                return SkillProfile(**data)
            except:
                return None
