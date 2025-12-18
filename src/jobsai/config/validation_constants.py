"""
Validation Constants for Frontend Payload Validation.

This module contains all validation constants used for validating frontend form submissions.
These constants define valid values, ranges, and constraints for various form fields.
"""

# Valid question set names (kebab-case)
VALID_QUESTION_SETS = {
    "general",
    "languages",
    "databases",
    "cloud-development",
    "web-frameworks",
    "dev-ides",
    "llms",
    "doc-and-collab",
    "operating-systems",
    "additional-info",
}

# Valid general question keys
VALID_GENERAL_KEYS = {
    "job-level",
    "job-boards",
    "deep-mode",
    "cover-letter-num",
    "cover-letter-style",
}

# Valid job level options
VALID_JOB_LEVELS = {"Expert-level", "Expert", "Intermediate", "Entry", "Intern"}

# Valid job board options
VALID_JOB_BOARDS = {"Duunitori", "Jobly", "Indeed"}

# Valid deep mode options
VALID_DEEP_MODE = {"Yes", "No"}

# Valid cover letter count range (now accepts integers, not strings)
# Frontend sends integers 1-10
VALID_COVER_LETTER_NUM_RANGE = range(1, 11)  # 1 to 10 inclusive

# Valid cover letter style options
VALID_COVER_LETTER_STYLE = {"Professional", "Friendly", "Confident", "Funny"}
