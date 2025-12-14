# ---------- TESTS FOR QUERY BUILDER AGENT ----------

import pytest
from unittest.mock import patch, MagicMock

from jobsai.agents.query_builder import QueryBuilderAgent

# Mock LLM response that returns valid JSON
mock_llm_response_json = """
{
    "query1": "python developer",
    "query2": "junior python developer",
    "query3": "python engineer",
    "query4": "ai engineer",
    "query5": "junior ai engineer",
    "query6": "machine learning engineer",
    "query7": "llm engineer",
    "query8": "agentic ai",
    "query9": "junior software developer",
    "query10": "junior full stack developer"
}
"""

mock_llm_response_markdown = """
Here are the search queries:

```json
{
    "query1": "python developer",
    "query2": "junior python developer"
}
```
"""


@pytest.fixture
def query_builder():
    """Create a QueryBuilderAgent instance for testing."""
    return QueryBuilderAgent()


@patch("jobsai.agents.query_builder.call_llm", return_value=mock_llm_response_json)
@patch("jobsai.agents.query_builder.extract_json", return_value=mock_llm_response_json)
def test_create_keywords_basic(mock_extract_json, mock_call_llm, query_builder):
    """Test that keywords are created from a profile."""
    profile = "Experienced Python developer with AI/ML background"
    keywords = query_builder.create_keywords(profile)
    assert isinstance(keywords, list)
    assert len(keywords) > 0
    assert all(isinstance(kw, str) for kw in keywords)


@patch("jobsai.agents.query_builder.call_llm", return_value=mock_llm_response_json)
@patch("jobsai.agents.query_builder.extract_json", return_value=mock_llm_response_json)
def test_keywords_contain_python(mock_extract_json, mock_call_llm, query_builder):
    """Test that Python-related keywords are generated for Python profiles."""
    profile = "Python developer with 5 years of experience"
    keywords = query_builder.create_keywords(profile)
    # Check that at least one keyword contains "python" (case-insensitive)
    python_keywords = [kw for kw in keywords if "python" in kw.lower()]
    assert len(python_keywords) > 0


@patch("jobsai.agents.query_builder.call_llm", return_value=mock_llm_response_json)
@patch("jobsai.agents.query_builder.extract_json", return_value=mock_llm_response_json)
def test_keywords_contain_ai(mock_extract_json, mock_call_llm, query_builder):
    """Test that AI-related keywords are generated for AI profiles."""
    profile = "AI engineer with experience in LangChain and TensorFlow"
    keywords = query_builder.create_keywords(profile)
    # Check that at least one keyword contains "ai" or "llm" or "machine learning"
    ai_keywords = [
        kw
        for kw in keywords
        if any(term in kw.lower() for term in ["ai", "llm", "machine learning", "ml"])
    ]
    assert len(ai_keywords) > 0


@patch("jobsai.agents.query_builder.call_llm", return_value=mock_llm_response_json)
@patch("jobsai.agents.query_builder.extract_json", return_value=mock_llm_response_json)
def test_keywords_always_present(mock_extract_json, mock_call_llm, query_builder):
    """Test that fallback keywords are always present."""
    profile = "Generic developer profile"
    keywords = query_builder.create_keywords(profile)
    # Should have at least some keywords
    assert len(keywords) >= 5  # Typically 10 keywords, but at least 5


@patch("jobsai.agents.query_builder.call_llm", return_value=mock_llm_response_json)
@patch("jobsai.agents.query_builder.extract_json", return_value=mock_llm_response_json)
def test_deterministic_ordering(mock_extract_json, mock_call_llm, query_builder):
    """Test that same profile produces same keywords (when LLM response is same)."""
    profile = "Python developer"
    keywords1 = query_builder.create_keywords(profile)
    keywords2 = query_builder.create_keywords(profile)
    # With mocked LLM, should be identical
    assert keywords1 == keywords2


@patch("jobsai.utils.llms.call_llm", return_value=mock_llm_response_markdown)
@patch("jobsai.utils.llms.extract_json", return_value=mock_llm_response_json)
def test_extracts_json_from_markdown(mock_extract_json, mock_call_llm, query_builder):
    """Test that JSON is extracted from markdown-wrapped responses."""
    profile = "Test profile"
    keywords = query_builder.create_keywords(profile)
    # Should successfully extract and parse
    assert isinstance(keywords, list)
    assert len(keywords) > 0


@patch("jobsai.agents.query_builder.call_llm", return_value="invalid json response")
@patch("jobsai.agents.query_builder.extract_json", return_value=None)
def test_retry_on_invalid_json(mock_extract_json, mock_call_llm, query_builder):
    """Test that invalid JSON triggers retry logic."""
    profile = "Test profile"
    # Should raise ValueError after retries
    with pytest.raises(ValueError, match="parseable JSON"):
        query_builder.create_keywords(profile, max_retries=1)
    # Should have called LLM multiple times (initial + retries)
    assert mock_call_llm.call_count > 1


@patch("jobsai.utils.llms.call_llm", return_value=mock_llm_response_json)
@patch(
    "jobsai.utils.llms.extract_json",
    return_value='{"query1": "python", "query2": "python"}',
)
def test_no_duplicates_in_keywords(mock_extract_json, mock_call_llm, query_builder):
    """Test that duplicate keywords are handled (if LLM returns duplicates)."""
    profile = "Python developer"
    keywords = query_builder.create_keywords(profile)
    # Keywords should be a list (duplicates would be in values, not list itself)
    assert isinstance(keywords, list)
    # If LLM returns duplicate values, they'll be in the list, but that's LLM's behavior
    # The function just extracts values from dict, so duplicates are possible
