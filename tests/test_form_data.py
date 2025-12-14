# ---------- TESTS FOR FORM DATA EXTRACTION ----------

import pytest

from jobsai.utils.form_data import extract_form_data


def test_extract_form_data_basic():
    """Test basic form data extraction."""
    form_submissions = {
        "general": [
            {"job-level": ["Expert"]},
            {"job-boards": ["Duunitori", "Jobly"]},
            {"deep-mode": "Yes"},
            {"cover-letter-num": 5},
            {"cover-letter-style": ["Professional", "Friendly"]},
        ],
        "languages": [{"python": 5}, {"javascript": 3}],
        "databases": [{"postgresql": 4}],
        "cloud-development": [{"docker": 3}],
        "web-frameworks": [{"react": 4}],
        "dev-ides": [{"vscode": 5}],
        "llms": [{"langchain": 2}],
        "doc-and-collab": [{"github": 5}],
        "operating-systems": [{"linux": 4}],
        "additional-info": [{"additional-info": "Test description"}],
    }
    result = extract_form_data(form_submissions)
    assert result["job_boards"] == ["Duunitori", "Jobly"]
    assert result["deep_mode"] == "Yes"
    assert result["cover_letter_num"] == 5
    assert result["cover_letter_style"] == ["Professional", "Friendly"]
    assert isinstance(result["tech_stack"], list)
    assert len(result["tech_stack"]) == 8  # 8 technology categories


def test_extract_form_data_tech_stack_structure():
    """Test that tech_stack has correct nested structure."""
    form_submissions = {
        "general": [
            {"job-level": ["Entry"]},
            {"job-boards": ["Duunitori"]},
            {"deep-mode": "No"},
            {"cover-letter-num": 1},
            {"cover-letter-style": ["Professional"]},
        ],
        "languages": [{"python": 3}, {"javascript": 2}],
        "databases": [{"postgresql": 1}],
        "cloud-development": [],
        "web-frameworks": [],
        "dev-ides": [],
        "llms": [],
        "doc-and-collab": [],
        "operating-systems": [],
        "additional-info": [{"additional-info": "Test"}],
    }
    result = extract_form_data(form_submissions)
    tech_stack = result["tech_stack"]
    # Should be list of lists
    assert isinstance(tech_stack, list)
    assert len(tech_stack) == 8
    # First category (languages) should have 2 items
    assert len(tech_stack[0]) == 2
    assert tech_stack[0] == [{"python": 3}, {"javascript": 2}]
    # Second category (databases) should have 1 item
    assert len(tech_stack[1]) == 1
    assert tech_stack[1] == [{"postgresql": 1}]
    # Empty categories should be empty lists
    assert tech_stack[2] == []  # cloud-development
    assert tech_stack[3] == []  # web-frameworks


def test_extract_form_data_missing_optional_categories():
    """Test extraction when optional technology categories are missing."""
    form_submissions = {
        "general": [
            {"job-level": ["Intermediate"]},
            {"job-boards": ["Jobly"]},
            {"deep-mode": "No"},
            {"cover-letter-num": 2},
            {"cover-letter-style": ["Confident"]},
        ],
        "languages": [{"python": 4}],
        "additional-info": [{"additional-info": "Minimal data"}],
    }
    result = extract_form_data(form_submissions)
    # Should still have 8 categories, with empty lists for missing ones
    assert len(result["tech_stack"]) == 8
    assert result["tech_stack"][0] == [{"python": 4}]  # languages
    # All other categories should be empty
    for i in range(1, 8):
        assert result["tech_stack"][i] == []


def test_extract_form_data_single_job_board():
    """Test extraction with single job board."""
    form_submissions = {
        "general": [
            {"job-level": ["Expert"]},
            {"job-boards": ["Duunitori"]},
            {"deep-mode": "Yes"},
            {"cover-letter-num": 3},
            {"cover-letter-style": ["Professional"]},
        ],
        "additional-info": [{"additional-info": "Test"}],
    }
    result = extract_form_data(form_submissions)
    assert result["job_boards"] == ["Duunitori"]
    assert isinstance(result["job_boards"], list)


def test_extract_form_data_single_cover_letter_style():
    """Test extraction with single cover letter style."""
    form_submissions = {
        "general": [
            {"job-level": ["Entry"]},
            {"job-boards": ["Duunitori"]},
            {"deep-mode": "No"},
            {"cover-letter-num": 1},
            {"cover-letter-style": ["Friendly"]},
        ],
        "additional-info": [{"additional-info": "Test"}],
    }
    result = extract_form_data(form_submissions)
    assert result["cover_letter_style"] == ["Friendly"]
    assert isinstance(result["cover_letter_style"], list)


def test_extract_form_data_integer_cover_letter_num():
    """Test that cover-letter-num is preserved as integer."""
    form_submissions = {
        "general": [
            {"job-level": ["Intermediate"]},
            {"job-boards": ["Duunitori"]},
            {"deep-mode": "No"},
            {"cover-letter-num": 7},  # Integer, not string
            {"cover-letter-style": ["Professional"]},
        ],
        "additional-info": [{"additional-info": "Test"}],
    }
    result = extract_form_data(form_submissions)
    assert result["cover_letter_num"] == 7
    assert isinstance(result["cover_letter_num"], int)


def test_extract_form_data_all_categories_populated():
    """Test extraction with all technology categories populated."""
    form_submissions = {
        "general": [
            {"job-level": ["Expert"]},
            {"job-boards": ["Duunitori", "Jobly"]},
            {"deep-mode": "Yes"},
            {"cover-letter-num": 10},
            {"cover-letter-style": ["Professional", "Confident"]},
        ],
        "languages": [{"python": 5}, {"javascript": 4}],
        "databases": [{"postgresql": 3}, {"mysql": 2}],
        "cloud-development": [{"docker": 4}, {"kubernetes": 2}],
        "web-frameworks": [{"react": 5}, {"django": 3}],
        "dev-ides": [{"vscode": 5}, {"pycharm": 3}],
        "llms": [{"langchain": 2}, {"openai": 1}],
        "doc-and-collab": [{"github": 5}, {"jira": 2}],
        "operating-systems": [{"linux": 4}, {"macos": 3}],
        "additional-info": [{"additional-info": "Comprehensive profile"}],
    }
    result = extract_form_data(form_submissions)
    # Check all categories have items
    for category in result["tech_stack"]:
        assert len(category) > 0
    # Verify specific counts
    assert len(result["tech_stack"][0]) == 2  # languages
    assert len(result["tech_stack"][1]) == 2  # databases
    assert len(result["tech_stack"][2]) == 2  # cloud-development
