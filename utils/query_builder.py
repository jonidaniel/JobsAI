# Input: The skill profile JSON
# Output: A priority-ordered list of job search queries, that's been deduplicated and normalized

# PSEUDO-RULES:

# For each language:
#     add "<language> developer"
#     add "junior <language> developer"
#     add "<language> engineer"

# For each agentic ai framework (e.g., LangChain):
#     add "<framework>"
#     add "<framework> developer"

# If AI/ML skills present:
#     add "ai engineer"
#     add "junior ai engineer"
#     add "machine learning engineer" (optional)

# Always add:
#     "junior software developer"
#     "junior full stack developer"
#     "entry level developer"
#     "llm engineer" (since you’re agentic AI focused)

def build_queries(skill_profile: dict) -> list[str]:
    """
    Build deterministic job search queries from a structured skill profile.
    This does NOT call an LLM — purely rule-based keyword generation.
    """

    queries = set()

    # 1. Core languages
    core_langs = skill_profile.get("core_languages", [])
    for lang in core_langs:
        l = lang.lower()
        queries.add(f"{l} developer")
        queries.add(f"junior {l} developer")
        queries.add(f"{l} engineer")

    # 2. Agentic AI experience
    agentic = skill_profile.get("agentic_ai_experience", [])
    for tool in agentic:
        t = tool.lower()
        queries.add(t)
        queries.add(f"{t} developer")

    # 3. AI/ML experience
    ai_ml = skill_profile.get("ai_ml_experience", [])
    if ai_ml:
        queries.add("ai engineer")
        queries.add("junior ai engineer")
        queries.add("machine learning engineer")

    # 4. General fallback queries (important for completeness)
    queries.add("junior software developer")
    queries.add("junior full stack developer")
    queries.add("entry level developer")

    # 5. Agentic AI / LLM-specific roles
    queries.add("llm engineer")
    queries.add("agentic ai")

    # Return sorted for determinism
    return sorted(queries)
