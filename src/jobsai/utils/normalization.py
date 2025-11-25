# ---------- NORMALIZATION FUNCTIONS ----------

# normalize_parsed
# normalize_list
# normalize_text
# _normalize_token

import re
from typing import List, Dict, Any

from config.schemas import SKILL_ALIAS_MAP

# ------------------------------
# Public interfaces
# ------------------------------


def normalize_parsed(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize the parsed JSON.

    Args:
        parsed: parsed skills JSON

    Returns:
        parsed: the normalized parsed skills JSON
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
    for k in keys:
        if k not in parsed:
            parsed[k] = (
                []
                if k != "experience_level"
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
        "AI/ML": int(el.get("AI/ML") or el.get("AI_ML") or 0),
    }
    parsed["experience_level"] = norm_el

    # Name normalization
    if not parsed.get("name") or not isinstance(parsed["name"], str):
        parsed["name"] = ""
    else:
        parsed["name"] = parsed["name"].strip()
    return parsed


def normalize_list(items: List[str]) -> List[str]:
    """
    Normalize list

    Args:
        items:

    Returns:
        normalized:
    """

    normalized = []
    seen = set()

    for item in items:
        if not isinstance(item, str):
            continue
        val = _normalize_token(item)
        if val and val not in seen:
            normalized.append(val)
            seen.add(val)

    return normalized


def normalize_text(text: str) -> str:
    """
    Safely normalize LLM-generated text by:
    - trimming leading/trailing whitespace
    - collapsing repeated blank lines
    - removing excessive indentation
    - normalizing line breaks
    - ensuring the text is readable and clean

    This function is intentionally conservative so it won't
    distort structured formats (like JSON or YAML).
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
def _normalize_token(tok: str) -> str:
    """
    Normalize token

    Args:
        tok:

    Returns:
        token:
        token.capitalize():
    """

    token = tok.strip()
    if not token:
        return token
    low = token.lower()
    if low in SKILL_ALIAS_MAP:
        return SKILL_ALIAS_MAP[low]
    # Basic capitalization rules
    if low.isupper():
        return token
    return token if any(c.isupper() for c in token) else token.capitalize()
