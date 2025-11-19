import pytest
from utils.query_builder import build_queries

def test_core_languages():
    skill_profile = {"core_languages": ["Python"]}
    queries = build_queries(skill_profile)
    assert "python developer" in queries
    assert "junior python developer" in queries
    assert "python engineer" in queries

def test_agentic_frameworks():
    skill_profile = {"agentic_ai_experience": ["LangChain"]}
    queries = build_queries(skill_profile)
    assert "langchain" in queries
    assert "langchain developer" in queries

def test_ai_ml_skills():
    skill_profile = {"ai_ml_experience": ["TensorFlow"]}
    queries = build_queries(skill_profile)
    assert "ai engineer" in queries
    assert "junior ai engineer" in queries
    assert "machine learning engineer" in queries

def test_fallback_queries_always_present():
    queries = build_queries({})
    for q in ["junior software developer", "junior full stack developer", "entry level developer"]:
        assert q in queries

def test_agentic_ai_roles_always_present():
    queries = build_queries({})
    for q in ["llm engineer", "agentic ai"]:
        assert q in queries

def test_deterministic_ordering():
    queries1 = build_queries({"core_languages": ["Python"]})
    queries2 = build_queries({"core_languages": ["Python"]})
    assert queries1 == queries2

def test_case_normalization():
    skill_profile = {"core_languages": ["PYTHON"]}
    queries = build_queries(skill_profile)
    assert "python developer" in queries

def test_no_duplicates():
    skill_profile = {"core_languages": ["Python", "python"]}
    queries = build_queries(skill_profile)
    assert queries.count("python developer") == 1
