"""
Form Data Extraction and Transformation Utilities.

This module provides utilities for extracting and transforming frontend form
submission data into a structured format suitable for the JobsAI pipeline.

The main function, extract_form_data(), processes the complex nested structure
from the frontend (grouped by question set) and extracts key configuration values
and technology experience data into a flat, pipeline-friendly format.

Extraction Process:
    1. Extracts general questions (job boards, deep mode, cover letter settings)
    2. Flattens technology experience sets into a single tech_stack array
    3. Validates and normalizes data types (strings to integers where needed)
    4. Returns structured dictionary ready for pipeline consumption

The extracted data is used by:
    - ProfilerAgent: To understand candidate preferences and experience
    - SearcherService: To determine which job boards to search
    - ScorerService: To match jobs against technology stack
    - GeneratorAgent: To determine cover letter count and style
"""

from typing import Dict, Any, List, Union


def extract_form_data(
    form_submissions: Dict[str, Any],
) -> Dict[str, Union[List[str], str, int, List[List[Dict[str, Union[int, str]]]]]]:
    """Extract and transform form submission data into structured format.

    Processes the frontend payload (validated FrontendPayload structure) to extract
    key configuration values and flatten technology experience data. Converts the
    nested question-set structure into a flat dictionary suitable for pipeline agents.

    Extraction Details:
        - General questions: Extracts from "general" array (5 required items)
        - Technology stack: Flattens all technology sets into single array of arrays
        - Data types: Converts cover-letter-num from string to integer
        - Normalization: Handles both array and string formats for cover-letter-style

    Args:
        form_submissions: Form data dictionary from frontend (validated FrontendPayload).
            Structure:
            {
                "general": [
                    {"job-level": ["Expert"]},
                    {"job-boards": ["Duunitori", "Jobly"]},
                    {"deep-mode": "Yes"},
                    {"cover-letter-num": "5"},
                    {"cover-letter-style": ["Professional"]}
                ],
                "languages": [{"javascript": 5}, {"python": 3}],
                "databases": [{"postgresql": 4}],
                ...
                "additional-info": [{"additional-info": "Personal description..."}]
            }

    Returns:
        Dictionary with extracted and transformed data:
        {
            "job_boards": List[str] - Selected job boards (e.g., ["Duunitori", "Jobly"])
            "deep_mode": str - "Yes" or "No" for full description fetching
            "cover_letter_num": int - Number of cover letters to generate (1-10)
            "cover_letter_style": List[str] - Writing styles (e.g., ["Professional", "Friendly"])
            "tech_stack": List[List[Dict]] - Technology experience grouped by category:
                [
                    [{"javascript": 5}, {"python": 3}],  # languages
                    [{"postgresql": 4}, {"mysql": 3}],  # databases
                    ...
                ]
        }

    Raises:
        KeyError: If required general question keys are missing.
        ValueError: If cover-letter-num cannot be converted to integer or is out of range.

    Note:
        The tech_stack is a list of lists, where each inner list represents one
        technology category (languages, databases, etc.). This structure allows
        the ScorerService to process each category separately for better matching.
    """

    # The selected job boards, deep mode setting, number of cover letters to generate, and style of the cover letters
    # Always an array, contains one or more strings
    job_boards = form_submissions.get("general")[1].get("job-boards")
    # Always a string, either "Yes" or "No"
    deep_mode = form_submissions.get("general")[2].get("deep-mode")
    # Always an integer, between 1 and 10
    cover_letter_num = form_submissions.get("general")[3].get("cover-letter-num")
    # Always an array of strings, contains one or more strings
    cover_letter_style = form_submissions.get("general")[4].get("cover-letter-style")

    # Extract technology categories into a tech stack list
    # Always an array of arrays, contains one or more arrays of technology set items
    tech_stack = [
        form_submissions.get("languages", []),
        form_submissions.get("databases", []),
        form_submissions.get("cloud-development", []),
        form_submissions.get("web-frameworks", []),
        form_submissions.get("dev-ides", []),
        form_submissions.get("llms", []),
        form_submissions.get("doc-and-collab", []),
        form_submissions.get("operating-systems", []),
    ]

    return {
        "job_boards": job_boards,
        "deep_mode": deep_mode,
        "cover_letter_num": cover_letter_num,
        "cover_letter_style": cover_letter_style,
        "tech_stack": tech_stack,
    }
