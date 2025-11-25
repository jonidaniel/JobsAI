# ---------- QUERY BUILDER ----------

# build_queries

# --- DESCRIPTION ---

# A deterministic keyword generator


def build_queries(skill_profile: dict) -> list[str]:
    """
    Build deterministic job search queries from a structured skill profile.

    Args:
        skill_profile: a candidate's skill profile, {
                                                      "name": "John Doe",
                                                      "core_languages": ["JavaScript", "Python"],
                                                      ...
                                                    }

    Returns:
        sorted(queries): a sorted list of search queries
    """

    queries = set()

    # Build search queries from core languages
    core_langs = skill_profile.get("core_languages", [])
    for lang in core_langs:
        l = lang.lower()
        queries.add(f"{l} developer")
        queries.add(f"junior {l} developer")
        queries.add(f"{l} engineer")

    # Build search queries from agentic AI experience
    agentic = skill_profile.get("agentic_ai_experience", [])
    for tool in agentic:
        t = tool.lower()
        queries.add(t)
        queries.add(f"{t} developer")

    # Build search queries from AI/ML experience
    ai_ml = skill_profile.get("ai_ml_experience", [])
    if ai_ml:
        queries.add("ai engineer")
        queries.add("junior ai engineer")
        queries.add("machine learning engineer")
        queries.add("ml engineer")

    # Add general fallback search queries
    queries.add("junior software developer")
    queries.add("junior full stack developer")
    queries.add("entry level developer")

    # Add other search queries
    queries.add("llm engineer")
    queries.add("agentic ai")

    return sorted(queries)
