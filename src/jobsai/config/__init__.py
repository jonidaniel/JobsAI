"""
Configuration Module for JobsAI.

This module provides backward compatibility by re-exporting all schemas and constants
from the split modules. The original schemas.py has been split into focused modules:

- request_schemas.py: FrontendPayload and request validation models
- profile_schemas.py: SkillProfile and ExperienceLevels
- validation_constants.py: All VALID_* constants
- prompts.py: OUTPUT_SCHEMA and other prompts

For new code, import directly from the focused modules:
    from jobsai.config.request_schemas import FrontendPayload
    from jobsai.config.profile_schemas import SkillProfile
    from jobsai.config.validation_constants import VALID_JOB_LEVELS
"""

# Re-export all schemas for backward compatibility
from jobsai.config.request_schemas import (
    FrontendPayload,
    GeneralQuestionItem,
    TechnologySetItem,
    AdditionalInfoItem,
)

from jobsai.config.profile_schemas import (
    SkillProfile,
    ExperienceLevels,
)

from jobsai.config.validation_constants import (
    VALID_QUESTION_SETS,
    VALID_GENERAL_KEYS,
    VALID_JOB_LEVELS,
    VALID_JOB_BOARDS,
    VALID_DEEP_MODE,
    VALID_COVER_LETTER_NUM_RANGE,
    VALID_COVER_LETTER_STYLE,
)

from jobsai.config.prompts import OUTPUT_SCHEMA

__all__ = [
    # Request schemas
    "FrontendPayload",
    "GeneralQuestionItem",
    "TechnologySetItem",
    "AdditionalInfoItem",
    # Profile schemas
    "SkillProfile",
    "ExperienceLevels",
    # Validation constants
    "VALID_QUESTION_SETS",
    "VALID_GENERAL_KEYS",
    "VALID_JOB_LEVELS",
    "VALID_JOB_BOARDS",
    "VALID_DEEP_MODE",
    "VALID_COVER_LETTER_NUM_RANGE",
    "VALID_COVER_LETTER_STYLE",
    # Prompts
    "OUTPUT_SCHEMA",
]
