# ---------- TESTS FOR ANALYZER AGENT ----------

import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from jobsai.agents.analyzer import AnalyzerAgent
from jobsai.utils.exceptions import CancellationError

# Mock data
mock_profile = "Experienced Python developer with 5 years of experience in web development and AI/ML."

mock_jobs = [
    {
        "title": "Senior Python Developer",
        "company": "Company A",
        "location": "Helsinki",
        "url": "https://example.com/job1",
        "score": 85,
        "matched_skills": ["Python", "JavaScript"],
        "missing_skills": ["Docker", "Kubernetes"],
        "description_snippet": "Looking for Python developer",
        "full_description": "We are looking for an experienced Python developer with knowledge of web frameworks and AI technologies.",
    },
    {
        "title": "AI Engineer",
        "company": "Company B",
        "location": "Espoo",
        "url": "https://example.com/job2",
        "score": 75,
        "matched_skills": ["Python", "AI/ML"],
        "missing_skills": ["TensorFlow"],
        "description_snippet": "AI engineer position",
        "full_description": "Join our AI team to work on cutting-edge machine learning projects.",
    },
]

mock_llm_instructions = """
Focus on highlighting your Python experience and web development background.
Emphasize your interest in AI/ML technologies and willingness to learn new tools.
Mention specific projects where you've applied these skills.
"""


@pytest.fixture
def analyzer():
    """Create an AnalyzerAgent instance for testing."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return AnalyzerAgent(timestamp)


@pytest.fixture(autouse=True)
def clean_job_analyses_folder():
    """Clean up job analyses folder before and after tests."""
    from jobsai.config.paths import JOB_ANALYSIS_PATH

    folder = JOB_ANALYSIS_PATH
    if os.path.exists(folder):
        for f in os.listdir(folder):
            file_path = os.path.join(folder, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
    else:
        os.makedirs(folder, exist_ok=True)
    yield
    # Cleanup after test
    if os.path.exists(folder):
        for f in os.listdir(folder):
            file_path = os.path.join(folder, f)
            if os.path.isfile(file_path):
                os.remove(file_path)


@patch("jobsai.agents.analyzer.call_llm", return_value=mock_llm_instructions)
def test_write_analysis_basic(mock_call_llm, analyzer):
    """Test that analysis is written for jobs."""
    analysis = analyzer.write_analysis(mock_jobs, mock_profile, analysis_size=2)
    assert isinstance(analysis, str)
    assert len(analysis) > 0
    assert "Job Analysis" in analysis
    assert "Top 2 Jobs:" in analysis
    assert mock_call_llm.called


@patch("jobsai.agents.analyzer.call_llm", return_value=mock_llm_instructions)
def test_write_analysis_includes_job_details(mock_call_llm, analyzer):
    """Test that analysis includes job details."""
    analysis = analyzer.write_analysis(mock_jobs, mock_profile, analysis_size=2)
    # Check that job details are included
    assert "Title: Senior Python Developer" in analysis
    assert "Company: Company A" in analysis
    assert "Location: Helsinki" in analysis
    assert "Score: 85%" in analysis
    assert "https://example.com/job1" in analysis


@patch("jobsai.agents.analyzer.call_llm", return_value=mock_llm_instructions)
def test_write_analysis_includes_skills(mock_call_llm, analyzer):
    """Test that analysis includes matched and missing skills."""
    analysis = analyzer.write_analysis(mock_jobs, mock_profile, analysis_size=2)
    assert "Matched Skills:" in analysis
    assert "Missing Skills:" in analysis
    assert "Python" in analysis or "Docker" in analysis


@patch("jobsai.agents.analyzer.call_llm", return_value=mock_llm_instructions)
def test_write_analysis_limits_to_analysis_size(mock_call_llm, analyzer):
    """Test that analysis is limited to analysis_size jobs."""
    analysis = analyzer.write_analysis(mock_jobs, mock_profile, analysis_size=1)
    # Should only include first job
    assert "Senior Python Developer" in analysis
    assert "AI Engineer" not in analysis
    # LLM should be called only once (for 1 job)
    assert mock_call_llm.call_count == 1


@patch("jobsai.agents.analyzer.call_llm", return_value=mock_llm_instructions)
def test_write_analysis_saves_to_disk(mock_call_llm, analyzer):
    """Test that analysis is saved to disk."""
    from jobsai.config.paths import JOB_ANALYSIS_PATH

    analysis = analyzer.write_analysis(mock_jobs, mock_profile, analysis_size=2)
    # Check that file was created
    files = os.listdir(JOB_ANALYSIS_PATH)
    assert len(files) > 0
    # Find the file with our timestamp
    matching_files = [f for f in files if analyzer.timestamp in f]
    assert len(matching_files) > 0
    # Verify file content
    file_path = os.path.join(JOB_ANALYSIS_PATH, matching_files[0])
    with open(file_path, "r", encoding="utf-8") as f:
        file_content = f.read()
        assert "Job Analysis" in file_content


@patch("jobsai.agents.analyzer.call_llm", return_value=mock_llm_instructions)
def test_write_analysis_handles_empty_jobs(mock_call_llm, analyzer):
    """Test that empty jobs list raises ValueError."""
    with pytest.raises(ValueError, match="No scored jobs found"):
        analyzer.write_analysis([], mock_profile, analysis_size=1)


@patch("jobsai.agents.analyzer.call_llm", return_value=mock_llm_instructions)
def test_write_analysis_uses_full_description_when_available(mock_call_llm, analyzer):
    """Test that full_description is used when available."""
    analyzer.write_analysis(mock_jobs, mock_profile, analysis_size=1)
    # Check that LLM was called with full_description
    call_args = mock_call_llm.call_args
    user_prompt = call_args[0][1]  # Second positional argument
    assert (
        "experienced Python developer" in user_prompt or "web frameworks" in user_prompt
    )


@patch("jobsai.agents.analyzer.call_llm", return_value=mock_llm_instructions)
def test_write_analysis_falls_back_to_snippet(mock_call_llm, analyzer):
    """Test that description_snippet is used when full_description is missing."""
    jobs_no_full = [
        {
            "title": "Python Developer",
            "company": "Company C",
            "location": "Tampere",
            "url": "https://example.com/job3",
            "score": 70,
            "matched_skills": ["Python"],
            "missing_skills": ["Docker"],
            "description_snippet": "Python developer needed",
        }
    ]
    analyzer.write_analysis(jobs_no_full, mock_profile, analysis_size=1)
    # Should still work with just snippet
    assert mock_call_llm.called


@patch("jobsai.agents.analyzer.call_llm", return_value=mock_llm_instructions)
def test_write_analysis_cancellation_check(mock_call_llm, analyzer):
    """Test that cancellation check works during analysis."""
    cancellation_called = False

    def cancellation_check():
        nonlocal cancellation_called
        cancellation_called = True
        return True

    with pytest.raises(CancellationError):
        analyzer.write_analysis(
            mock_jobs,
            mock_profile,
            analysis_size=2,
            cancellation_check=cancellation_check,
        )
    assert cancellation_called


@patch("jobsai.agents.analyzer.call_llm", return_value=mock_llm_instructions)
def test_write_analysis_handles_missing_fields(mock_call_llm, analyzer):
    """Test that analysis handles jobs with missing optional fields."""
    jobs_minimal = [
        {
            "title": "Developer",
            "score": 60,
            "description_snippet": "Developer position",
        }
    ]
    analysis = analyzer.write_analysis(jobs_minimal, mock_profile, analysis_size=1)
    # Should still work, using "N/A" for missing fields
    assert "Title: Developer" in analysis
    assert "Company: N/A" in analysis or "Location: N/A" in analysis
