# ---------- NORMALIZATION FUNCTIONS ----------

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
