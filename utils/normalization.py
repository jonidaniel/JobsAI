# ---------- NORMALIZATION HELPERS ----------

from typing import List

SKILL_ALIAS_MAP = {
    "py": "Python",
    "python3": "Python",
    "python": "Python",
    "js": "JavaScript",
    "node": "Node.js",
    "nodejs": "Node.js",
    "reactjs": "React",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "postgres": "PostgreSQL",
    "sql": "SQL",
}

def normalize_token(tok: str) -> str:
    t = tok.strip()
    if not t:
        return t
    low = t.lower()
    if low in SKILL_ALIAS_MAP:
        return SKILL_ALIAS_MAP[low]
    # Basic capitalization rules
    if low.isupper():
        return t
    return t if any(c.isupper() for c in t) else t.capitalize()

def normalize_list(items: List[str]) -> List[str]:
    normalized = []
    seen = set()
    for it in items:
        if not isinstance(it, str):
            continue
        val = normalize_token(it)
        if val and val not in seen:
            normalized.append(val)
            seen.add(val)
    return normalized
