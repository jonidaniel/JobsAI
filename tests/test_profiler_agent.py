# ---------- TESTS FOR PROFILER AGENT ----------

import pytest
from unittest.mock import patch, MagicMock

from jobsai.agents.profiler import ProfilerAgent

# Mock LLM response
mock_profile_response = """
John Doe is an experienced software engineer with 5 years of experience in Python and JavaScript.
He has strong skills in web development, AI/ML technologies, and cloud platforms.
He prefers working in collaborative environments and values continuous learning.
"""


@pytest.fixture
def profiler():
    """Create a ProfilerAgent instance for testing."""
    return ProfilerAgent()


@patch("jobsai.agents.profiler.call_llm", return_value=mock_profile_response)
def test_create_profile_basic(mock_call_llm, profiler):
    """Test that profile is created from form submissions."""
    form_submissions = {
        "general": [
            {"job-level": ["Expert"]},
            {"job-boards": ["Duunitori"]},
            {"deep-mode": "Yes"},
            {"cover-letter-num": 5},
            {"cover-letter-style": ["Professional"]},
        ],
        "languages": [{"python": 5}, {"javascript": 3}],
        "additional-info": [{"additional-info": "Experienced developer"}],
    }
    profile = profiler.create_profile(form_submissions)
    assert isinstance(profile, str)
    assert len(profile) > 0
    assert mock_call_llm.called


@patch("jobsai.agents.profiler.call_llm", return_value=mock_profile_response)
def test_create_profile_returns_string(mock_call_llm, profiler):
    """Test that create_profile returns a string."""
    form_submissions = {
        "general": [
            {"job-level": ["Entry"]},
            {"job-boards": ["Jobly"]},
            {"deep-mode": "No"},
            {"cover-letter-num": 1},
            {"cover-letter-style": ["Friendly"]},
        ],
        "languages": [{"python": 2}],
        "additional-info": [{"additional-info": "Junior developer"}],
    }
    profile = profiler.create_profile(form_submissions)
    assert isinstance(profile, str)


@patch("jobsai.agents.profiler.call_llm", return_value=mock_profile_response)
def test_create_profile_calls_llm_with_form_data(mock_call_llm, profiler):
    """Test that LLM is called with form submission data."""
    form_submissions = {
        "general": [
            {"job-level": ["Intermediate"]},
            {"job-boards": ["Duunitori", "Jobly"]},
            {"deep-mode": "Yes"},
            {"cover-letter-num": 3},
            {"cover-letter-style": ["Professional", "Confident"]},
        ],
        "languages": [{"python": 4}, {"javascript": 3}],
        "databases": [{"postgresql": 2}],
        "additional-info": [{"additional-info": "Mid-level developer"}],
    }
    profiler.create_profile(form_submissions)
    # Verify LLM was called
    assert mock_call_llm.called
    # Check that form_submissions were passed in the user prompt
    call_args = mock_call_llm.call_args
    user_prompt = call_args[0][1]  # Second positional argument is user_prompt
    assert "form_submissions" in user_prompt or str(form_submissions) in user_prompt


@patch("jobsai.agents.profiler.call_llm", return_value="Short profile")
def test_create_profile_handles_short_responses(mock_call_llm, profiler):
    """Test that short LLM responses are handled correctly."""
    form_submissions = {
        "general": [
            {"job-level": ["Entry"]},
            {"job-boards": ["Duunitori"]},
            {"deep-mode": "No"},
            {"cover-letter-num": 1},
            {"cover-letter-style": ["Professional"]},
        ],
        "additional-info": [{"additional-info": "Minimal info"}],
    }
    profile = profiler.create_profile(form_submissions)
    assert isinstance(profile, str)
    assert profile == "Short profile"


@patch("jobsai.agents.profiler.call_llm", side_effect=Exception("LLM API error"))
def test_create_profile_handles_llm_errors(mock_call_llm, profiler):
    """Test that LLM errors are propagated."""
    form_submissions = {
        "general": [
            {"job-level": ["Expert"]},
            {"job-boards": ["Duunitori"]},
            {"deep-mode": "Yes"},
            {"cover-letter-num": 5},
            {"cover-letter-style": ["Professional"]},
        ],
        "additional-info": [{"additional-info": "Test"}],
    }
    with pytest.raises(Exception, match="LLM API error"):
        profiler.create_profile(form_submissions)


@patch("jobsai.agents.profiler.call_llm", return_value=mock_profile_response)
def test_create_profile_with_empty_tech_stack(mock_call_llm, profiler):
    """Test profile creation with minimal form data."""
    form_submissions = {
        "general": [
            {"job-level": ["Entry"]},
            {"job-boards": ["Duunitori"]},
            {"deep-mode": "No"},
            {"cover-letter-num": 1},
            {"cover-letter-style": ["Professional"]},
        ],
        "additional-info": [{"additional-info": "Just starting out"}],
    }
    profile = profiler.create_profile(form_submissions)
    assert isinstance(profile, str)
    assert len(profile) > 0
