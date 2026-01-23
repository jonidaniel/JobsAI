"""
Text and Data Normalization Utilities.

This module provides functions for normalizing text, lists, and structured data
throughout the JobsAI pipeline. Normalization ensures consistency in:
- Technology name capitalization and aliasing
- List deduplication
- Text formatting (whitespace, line breaks)
- Skill profile structure validation

Functions:
    normalize_parsed: Normalize and validate parsed skill profile dictionaries
    normalize_list: Deduplicate and standardize capitalization in skill lists
    normalize_text: Clean and format LLM-generated text
    _normalize_token: Internal function for token-level normalization
"""

import re
from typing import List, Dict, Any, Union

from jobsai.config.aliases import SKILL_ALIAS_MAP

# ------------------------------
# Public interfaces
# ------------------------------


def normalize_parsed(profile_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize and validate parsed skill profile dictionary.

    Processes the JSON dictionary returned by the LLM to ensure all expected
    keys are present and properly formatted. Adds missing keys with empty
    defaults to maintain consistent structure.

    Args:
        profile_dict: Parsed skills JSON dictionary from LLM containing
            candidate profile data (name, skills, experience levels, etc.).

    Returns:
        Dict[str, Any]: Normalized profile dictionary with all expected keys
            present, even if originally missing (filled with empty defaults).
    """

    keys = [
        "name",
        "core_languages",
        "frameworks_and_libraries",
        "tools_and_platforms",
        "agentic_ai_experience",
        "ai_ml_experience",
        "soft_skills",
        "projects_mentioned",
        "experience_level",
        "job_search_keywords",
    ]
    # Ensure all keys exist in the JSON the LLM generated
    for field_name in keys:
        if field_name not in profile_dict:
            profile_dict[field_name] = (
                []
                if field_name != "experience_level"
                else {"Python": 0, "JavaScript": 0, "Agentic AI": 0, "AI/ML": 0}
            )

    # Normalize lists
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
        if isinstance(profile_dict.get(list_key), list):
            profile_dict[list_key] = normalize_list(profile_dict[list_key])
        else:
            profile_dict[list_key] = []

    # Normalize experience_level keys and values
    experience_levels = profile_dict.get("experience_level", {})
    normalized_experience_levels = {
        "Python": int(experience_levels.get("Python") or 0),
        "JavaScript": int(experience_levels.get("JavaScript") or 0),
        "Agentic AI": int(
            experience_levels.get("Agentic AI")
            or experience_levels.get("Agentic_Ai")
            or 0
        ),
        "AI/ML": int(
            experience_levels.get("AI/ML") or experience_levels.get("AI_ML") or 0
        ),
    }
    profile_dict["experience_level"] = normalized_experience_levels

    # Name normalization
    if not profile_dict.get("name") or not isinstance(profile_dict["name"], str):
        profile_dict["name"] = ""
    else:
        profile_dict["name"] = profile_dict["name"].strip()
    return profile_dict


def normalize_list(skill_items: List[str]) -> List[str]:
    """Normalize list of skill items by deduplicating and standardizing capitalization.

    Processes a list of skill/item strings to remove duplicates and apply consistent
    capitalization. Uses skill aliases to map variations to canonical names.

    Args:
        skill_items: List of skill/item strings to normalize. May contain duplicates
            and inconsistent capitalization.

    Returns:
        List[str]: Normalized list with duplicates removed, proper capitalization
            applied, and aliases resolved to canonical names.
    """

    normalized = []
    seen = set()

    for item in skill_items:
        if not isinstance(item, str):
            continue
        normalized_value = _normalize_token(item)
        if normalized_value and normalized_value not in seen:
            normalized.append(normalized_value)
            seen.add(normalized_value)

    return normalized


def normalize_text(text: str) -> str:
    """Safely normalize LLM-generated text.

    Cleans and formats text output from LLM calls by:
    - Trimming leading/trailing whitespace
    - Collapsing repeated blank lines
    - Normalizing line breaks (CRLF → LF)
    - Removing trailing spaces from lines
    - Ensuring the text is readable and clean

    This function is intentionally conservative so it won't
    distort structured formats (like JSON or YAML).

    Args:
        text: Raw text string from LLM that may contain formatting inconsistencies.

    Returns:
        str: Normalized text with consistent formatting. Returns the input unchanged
            if it's not a string.
    """

    if not isinstance(text, str):
        return text

    # Convert CRLF → LF
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove trailing spaces from lines
    text = "\n".join(line.rstrip() for line in text.split("\n"))

    # Collapse multiple blank lines → one
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

    # Remove leading/trailing blank lines
    text = text.strip()

    return text


# ------------------------------
# Internal function
# ------------------------------
def _normalize_token(token: str) -> str:
    """Normalize a single token string.

    Applies normalization rules to a single token:
    - Strips whitespace
    - Maps aliases to canonical names (via SKILL_ALIAS_MAP)
    - Applies title case capitalization

    Args:
        token: The token string to normalize.

    Returns:
        str: The normalized token with proper capitalization and alias resolution.
            Returns empty string if token is empty after stripping.
    """

    token = token.strip()
    if not token:
        return token
    token_lowercase = token.lower()
    if token_lowercase in SKILL_ALIAS_MAP:
        return SKILL_ALIAS_MAP[token_lowercase]
    # Basic capitalization rules
    if token_lowercase.isupper():
        return token
    return token if any(c.isupper() for c in token) else token.capitalize()
