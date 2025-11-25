# ---------- NORMALIZATION FUNCTIONS ----------

# normalize_token
# normalize_list
# normalize_text

import re
from typing import List

from config.schemas import SKILL_ALIAS_MAP


def normalize_token(tok: str) -> str:
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
        val = normalize_token(item)
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
