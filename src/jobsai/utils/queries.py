"""
JobsAI/src/jobsai/utils/queries.py

Query builder. Deterministic keyword generator.

    build_queries
"""


def build_queries(skill_profile: dict) -> list[str]:
    """
    Build deterministic job search queries from a structured skill profile.

    This function generates search queries that will be used to scrape job boards.
    The queries are built deterministically from the skill profile to ensure
    consistent results across runs.

    Query generation strategy:
    - Core languages: Generate "{lang} developer", "junior {lang} developer", "{lang} engineer"
    - Agentic AI tools: Generate tool name and "{tool} developer"
    - AI/ML experience: Generate general AI/ML job queries
    - Fallback queries: Always include general entry-level queries
    - Specialized queries: Always include LLM and agentic AI queries

    Args:
        skill_profile (dict): A candidate's skill profile dictionary containing:
            - "core_languages": List of programming languages
            - "agentic_ai_experience": List of agentic AI tools/technologies
            - "ai_ml_experience": List of AI/ML technologies
            - Other fields are not used for query generation

    Returns:
        list[str]: A sorted list of unique search query strings
    """

    queries = set()  # Use set to automatically deduplicate queries

    # Build search queries from core programming languages
    # Generates multiple query variations for each language
    core_langs = skill_profile.get("core_languages", [])
    for lang in core_langs:
        l = lang.lower()
        queries.add(f"{l} developer")
        queries.add(f"junior {l} developer")
        queries.add(f"{l} engineer")

    # Build search queries from agentic AI experience
    # These are specialized tools/technologies that warrant specific searches
    agentic = skill_profile.get("agentic_ai_experience", [])
    for tool in agentic:
        t = tool.lower()
        queries.add(t)  # Direct tool name search
        queries.add(f"{t} developer")  # Tool + developer search

    # Build search queries from AI/ML experience
    # If candidate has any AI/ML experience, add general AI/ML job queries
    ai_ml = skill_profile.get("ai_ml_experience", [])
    if ai_ml:
        queries.add("ai engineer")
        queries.add("junior ai engineer")
        queries.add("machine learning engineer")
        queries.add("ml engineer")

    # Add general fallback search queries
    # These ensure we always search for entry-level positions
    queries.add("junior software developer")
    queries.add("junior full stack developer")
    queries.add("entry level developer")

    # Add specialized queries that are always relevant
    # These target emerging fields that may not be in the profile
    queries.add("llm engineer")
    queries.add("agentic ai")

    # Return sorted list for deterministic output
    return sorted(queries)
