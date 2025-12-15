"""
Pydantic Schemas for Frontend Payload Validation and Data Transformation.

This module defines Pydantic models for validating and transforming frontend form data.
It handles the conversion between frontend kebab-case keys and backend snake_case,
and validates data types and constraints.

Key Models:
    - FrontendPayload: Main model for validating complete form submissions
    - GeneralQuestionItem: Validates general questions (job level, boards, etc.)
    - TechnologySetItem: Validates technology experience levels (sliders)
    - AdditionalInfoItem: Validates personal description field
    - ExperienceLevels: Maps numeric experience values to descriptive strings
    - SkillProfile: Structure for candidate skill profiles

Note:
    All models use Pydantic's Field validation and model_validator for complex
    validation logic. The ConfigDict enables alias generation for kebab-case keys
    to match frontend naming conventions.

    For alias mappings (EXPERIENCE_ALIAS_MAP, SKILL_ALIAS_MAP, SUBMIT_ALIAS_MAP),
    see jobsai.config.aliases module.
"""

from typing import List, Dict, Any, Optional

from pydantic import (
    BaseModel,
    Field,
    model_validator,
    field_validator,
    ConfigDict,
    EmailStr,
)

# Import alias mappings from separate module
from jobsai.config.aliases import (
    EXPERIENCE_ALIAS_MAP,
    SKILL_ALIAS_MAP,
    SUBMIT_ALIAS_MAP,
)

# ----- PROMPTING -----

OUTPUT_SCHEMA = """{
  "name": STRING VALUE,
  "core_languages": [STRING VALUE(S)],
  "frameworks_and_libraries": [STRING VALUE(S)],
  "tools_and_platforms": [STRING VALUE(S)],
  "agentic_ai_experience": [STRING VALUE(S)],
  "ai_ml_experience": [STRING VALUE(S)],
  "soft_skills": [STRING VALUE(S)],
  "projects_mentioned": [STRING VALUE(S)],
  "experience_level": {
      "Python": INTEGER VALUE,
      "JavaScript": INTEGER VALUE,
      "Agentic AI": INTEGER VALUE,
      "AI/ML": INTEGER VALUE
  },
  "job_search_keywords": [STRING VALUE(S)]
}"""

# ----- PYDANTIC -----


class ExperienceLevels(BaseModel):
    """
    Experience level ratings for key technology areas.

    Values represent years of experience on a scale:
    - 0: No experience
    - 1: Less than half a year
    - 2: Less than a year
    - 3: Less than 1.5 years
    - 4: Less than 2 years
    - 5: Less than 2.5 years
    - 6: Less than 3 years
    - 7: Over 3 years

    Fields use aliases to support both Python naming conventions and
    display-friendly names (e.g., "Agentic AI" contains a space).
    """

    Python: int = 0
    JavaScript: int = 0
    Agentic_Ai: int = Field(0, alias="Agentic AI")
    AI_ML: int = Field(0, alias="AI/ML")

    model_config = ConfigDict(
        # Allows access by both field name and alias
        populate_by_name=True,
        # Example values for API documentation
        json_schema_extra={
            "example": {"Python": 7, "JavaScript": 6, "Agentic AI": 5, "AI/ML": 4}
        },
    )


class SkillProfile(BaseModel):
    """
    A candidate's comprehensive skill profile.

    This is the central data structure that represents a candidate's skills,
    experience, and qualifications. It's created by the ProfilerAgent from
    form submissions and used throughout the pipeline for:
    - Generating job search queries
    - Scoring job relevancy
    - Writing personalized cover letters

    All list fields are automatically deduplicated and normalized during processing.
    """

    name: str = ""  # Candidate's name (optional)
    core_languages: List[str] = []  # Programming languages (Python, JavaScript, etc.)
    frameworks_and_libraries: List[str] = (
        []
    )  # Frameworks and libraries (React, FastAPI, etc.)
    tools_and_platforms: List[str] = []  # Tools and platforms (Docker, AWS, etc.)
    agentic_ai_experience: List[str] = []  # Agentic AI tools/technologies
    ai_ml_experience: List[str] = []  # AI/ML technologies and tools
    soft_skills: List[str] = []  # Soft skills (communication, teamwork, etc.)
    projects_mentioned: List[str] = []  # Project names/titles mentioned
    experience_level: ExperienceLevels = Field(
        default_factory=ExperienceLevels
    )  # Experience ratings
    job_search_keywords: List[str] = []  # Additional keywords for job searching

    model_config = ConfigDict(
        # Allows access by both field name and alias
        populate_by_name=True,
    )


# ----- FRONTEND PAYLOAD VALIDATION -----

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
VALID_JOB_BOARDS = {"Duunitori", "Jobly"}

# Valid deep mode options
VALID_DEEP_MODE = {"Yes", "No"}

# Valid cover letter count range (now accepts integers, not strings)
# Frontend sends integers 1-10
VALID_COVER_LETTER_NUM_RANGE = range(1, 11)  # 1 to 10 inclusive

# Valid cover letter style options
VALID_COVER_LETTER_STYLE = {"Professional", "Friendly", "Confident", "Funny"}


class GeneralQuestionItem(BaseModel):
    """
    Validates a single general question item (single-key dictionary).

    Examples:
        {"job-level": ["Expert", "Intermediate"]}
        {"deep-mode": "Yes"}
    """

    @model_validator(mode="before")
    @classmethod
    def validate_single_key_dict(cls, data: Any) -> Dict[str, Any]:
        """Ensure the item is a single-key dictionary."""
        if not isinstance(data, dict):
            raise ValueError("General question item must be a dictionary")
        if len(data) != 1:
            raise ValueError(
                "General question item must contain exactly one key-value pair"
            )
        return data

    @field_validator("*", mode="before")
    @classmethod
    def validate_value_type(cls, v: Any, info) -> Any:
        """Validate the value type based on the key."""
        key = list(info.data.keys())[0] if isinstance(info.data, dict) else None

        if key == "job-level":
            if not isinstance(v, list) or len(v) == 0:
                raise ValueError(
                    "job-level must be a non-empty array with at least one option"
                )
            if len(v) > 2:
                raise ValueError("job-level must contain at most 2 options")
            invalid = [x for x in v if x not in VALID_JOB_LEVELS]
            if invalid:
                raise ValueError(
                    f"Invalid job-level options: {invalid}. Valid options: {VALID_JOB_LEVELS}"
                )
            # If 2 options selected, they must be adjacent
            if len(v) == 2:
                valid_pairs = [
                    {"Expert-level", "Intermediate"},
                    {
                        "Expert",
                        "Intermediate",
                    },  # Also accept "Expert" for backward compatibility
                    {"Intermediate", "Entry"},
                    {"Entry", "Intern"},
                ]
                option_set = set(v)
                if not any(option_set == pair for pair in valid_pairs):
                    raise ValueError(
                        "If selecting two job levels, they must be adjacent "
                        "(Expert-level + Intermediate, Intermediate + Entry, or Entry + Intern)"
                    )
        elif key == "job-boards":
            if not isinstance(v, list) or len(v) == 0:
                raise ValueError(
                    "job-boards must be a non-empty array with at least one option"
                )
            invalid = [x for x in v if x not in VALID_JOB_BOARDS]
            if invalid:
                raise ValueError(
                    f"Invalid job-board options: {invalid}. Valid options: {VALID_JOB_BOARDS}"
                )
        elif key == "deep-mode":
            if not isinstance(v, str) or v not in VALID_DEEP_MODE:
                raise ValueError(f"deep-mode must be one of: {VALID_DEEP_MODE}")
        elif key == "cover-letter-num":
            # Accept integer values (frontend now sends integers, not strings)
            # Also accept string values for backward compatibility and convert to int
            try:
                # Convert to integer (handles both int and string "5")
                cover_letter_num = int(v) if not isinstance(v, int) else v
                # Validate range (1-10)
                if cover_letter_num not in VALID_COVER_LETTER_NUM_RANGE:
                    raise ValueError(
                        f"cover-letter-num must be between 1 and 10, got {cover_letter_num}"
                    )
                # Return as integer
                return cover_letter_num
            except (ValueError, TypeError) as e:
                if isinstance(e, ValueError) and "between 1 and 10" in str(e):
                    raise  # Re-raise range errors
                raise ValueError(
                    f"cover-letter-num must be a number between 1 and 10, got {v} (type: {type(v).__name__})"
                ) from e
        elif key == "cover-letter-style":
            if not isinstance(v, list) or len(v) == 0:
                raise ValueError(
                    "cover-letter-style must be a non-empty array with at least one option"
                )
            if len(v) > 2:
                raise ValueError("cover-letter-style must contain at most 2 options")
            invalid = [x for x in v if x not in VALID_COVER_LETTER_STYLE]
            if invalid:
                raise ValueError(
                    f"Invalid cover-letter-style options: {invalid}. Valid options: {VALID_COVER_LETTER_STYLE}"
                )
        else:
            raise ValueError(
                f"Invalid general question key: {key}. Valid keys: {VALID_GENERAL_KEYS}"
            )

        return v

    model_config = ConfigDict(
        extra="allow"
    )  # Allow dynamic keys since we validate structure in model_validator


class TechnologySetItem(BaseModel):
    """
    Validates a single technology set item (single-key dictionary).

    Examples:
        {"javascript": 5}  # Slider value (0-7)
        {"text-field1": "Additional languages..."}  # Text field (string)
    """

    @model_validator(mode="before")
    @classmethod
    def validate_single_key_dict(cls, data: Any) -> Dict[str, Any]:
        """Ensure the item is a single-key dictionary."""
        if not isinstance(data, dict):
            raise ValueError("Technology set item must be a dictionary")
        if len(data) != 1:
            raise ValueError(
                "Technology set item must contain exactly one key-value pair"
            )
        return data

    @field_validator("*", mode="before")
    @classmethod
    def validate_value_type(cls, v: Any, info) -> Any:
        """Validate the value type based on the key."""
        key = list(info.data.keys())[0] if isinstance(info.data, dict) else None

        if key and key.startswith("text-field"):
            # Text field: must be a string (can be empty for optional fields)
            if not isinstance(v, str):
                raise ValueError(f"Text field '{key}' must be a string")
            # Validate length: max 50 characters
            if len(v) > 50:
                raise ValueError(
                    f"Text field '{key}' must be at most 50 characters, got {len(v)}"
                )
        else:
            # Slider value: must be an integer 0-7
            if not isinstance(v, int) or v < 0 or v > 7:
                raise ValueError(
                    f"Slider value for '{key}' must be an integer between 0 and 7, got: {v}"
                )

        return v

    model_config = ConfigDict(
        extra="allow"
    )  # Allow dynamic keys since we validate structure in model_validator


class AdditionalInfoItem(BaseModel):
    """
    Validates the additional-info question set item.

    Example:
        {"additional-info": "Personal description..."}
    """

    @model_validator(mode="before")
    @classmethod
    def validate_single_key_dict(cls, data: Any) -> Dict[str, Any]:
        """Ensure the item is a single-key dictionary with 'additional-info' key and non-empty value."""
        if not isinstance(data, dict):
            raise ValueError("Additional info item must be a dictionary")
        if len(data) != 1:
            raise ValueError(
                "Additional info item must contain exactly one key-value pair"
            )
        if "additional-info" not in data:
            raise ValueError("Additional info item must have key 'additional-info'")

        # Validate the value is a non-empty string
        value = data["additional-info"]
        if not isinstance(value, str):
            raise ValueError("additional-info must be a string")
        if value.strip() == "":
            raise ValueError("additional-info cannot be empty")
        # Validate length: max 3000 characters
        if len(value) > 3000:
            raise ValueError(
                f"additional-info must be at most 3000 characters, got {len(value)}"
            )

        return data

    model_config = ConfigDict(
        extra="allow"
    )  # Allow dynamic keys since we validate structure in model_validator


class FrontendPayload(BaseModel):
    """Validates the complete frontend payload structure.

    Main Pydantic model for validating form submissions from the frontend.
    The payload is grouped by question set, where each question set contains
    an array of single-key objects representing individual form fields.

    Required Fields:
        - general: Exactly 5 items (job-level, job-boards, deep-mode, cover-letter-num, cover-letter-style)
        - additional-info: Exactly 1 item (personal description, max 3000 characters)

    Optional Fields (technology experience sets):
        - languages: Programming languages (max 42 items)
        - databases: Database technologies (max 30 items)
        - cloud-development: Cloud platforms and tools (max 42 items)
        - web-frameworks: Web frameworks (max 28 items)
        - dev-ides: Development IDEs (max 27 items)
        - llms: Large language models (max 17 items)
        - doc-and-collab: Documentation and collaboration tools (max 25 items)
        - operating-systems: Operating systems (max 12 items)

    Structure:
        {
            "general": [
                {"job-level": ["Expert", "Intermediate"]},
                {"job-boards": ["Duunitori", "Jobly"]},
                {"deep-mode": "Yes"},
                {"cover-letter-num": 5},
                {"cover-letter-style": ["Professional"]}
            ],
            "languages": [
                {"javascript": 5},
                {"python": 3},
                {"text-field1": "TypeScript"}
            ],
            ...
            "additional-info": [
                {"additional-info": "I am a software engineer with 5 years..."}
            ]
        }

    Validation:
        - All general questions are required and validated
        - Technology sets are optional but validated if present
        - Experience values must be integers 0-7
        - Custom text fields are validated for length and content
        - Additional info must be non-empty string (max 3000 chars)

    Note:
        Uses Pydantic aliases to handle kebab-case keys from frontend while
        maintaining snake_case in Python code. The model_validator ensures
        the structure matches expected format.
    """

    general: List[GeneralQuestionItem] = Field(
        ..., min_length=5, max_length=5, description="General questions (5 required)"
    )
    languages: List[TechnologySetItem] = Field(
        default_factory=list,
        max_length=42,
        description="Programming languages experience (max 42 items)",
    )
    databases: List[TechnologySetItem] = Field(
        default_factory=list,
        max_length=30,
        description="Databases experience (max 30 items)",
    )
    cloud_development: List[TechnologySetItem] = Field(
        default_factory=list,
        max_length=42,
        alias="cloud-development",
        description="Cloud development experience (max 42 items)",
    )
    web_frameworks: List[TechnologySetItem] = Field(
        default_factory=list,
        max_length=28,
        alias="web-frameworks",
        description="Web frameworks experience (max 28 items)",
    )
    dev_ides: List[TechnologySetItem] = Field(
        default_factory=list,
        max_length=27,
        alias="dev-ides",
        description="Dev IDEs experience (max 27 items)",
    )
    llms: List[TechnologySetItem] = Field(
        default_factory=list,
        max_length=17,
        description="Large language models experience (max 17 items)",
    )
    doc_and_collab: List[TechnologySetItem] = Field(
        default_factory=list,
        max_length=25,
        alias="doc-and-collab",
        description="Documentation and collaboration experience (max 25 items)",
    )
    operating_systems: List[TechnologySetItem] = Field(
        default_factory=list,
        max_length=15,
        alias="operating-systems",
        description="Operating systems experience (max 15 items)",
    )
    additional_info: List[AdditionalInfoItem] = Field(
        ...,
        min_length=1,
        max_length=1,
        alias="additional-info",
        description="Personal description (required)",
    )
    delivery_method: Optional[str] = Field(
        None,
        description="Delivery method: 'email' or 'download'",
    )
    email: Optional[str] = Field(
        None,
        description="Email address for email delivery (required if delivery_method is 'email')",
    )

    @model_validator(mode="after")
    def validate_general_questions(self) -> "FrontendPayload":
        """Validate that all 5 general questions are present with correct keys."""
        general_keys = set()
        for item in self.general:
            # Each item is a dict with one key
            item_dict = item.model_dump()
            key = list(item_dict.keys())[0]
            general_keys.add(key)

        required_keys = VALID_GENERAL_KEYS
        missing = required_keys - general_keys
        if missing:
            raise ValueError(
                f"Missing required general questions: {missing}. "
                f"All 5 questions are required: {required_keys}"
            )

        # Check for duplicates
        if len(general_keys) < len(self.general):
            raise ValueError("Duplicate general question keys found")

        return self

    @model_validator(mode="after")
    def validate_additional_info(self) -> "FrontendPayload":
        """Validate that additional-info is present and non-empty."""
        if not self.additional_info or len(self.additional_info) == 0:
            raise ValueError("additional-info is required and cannot be empty")

        # Extract the value from the single-key dict
        info_item = self.additional_info[0]
        info_dict = info_item.model_dump()
        if "additional-info" not in info_dict:
            raise ValueError("additional-info item must have key 'additional-info'")

        info_value = info_dict["additional-info"]
        if (
            not info_value
            or not isinstance(info_value, str)
            or info_value.strip() == ""
        ):
            raise ValueError("additional-info cannot be empty")

        return self

    @model_validator(mode="after")
    def validate_delivery_method(self) -> "FrontendPayload":
        """Validate delivery method and email if provided."""
        if self.delivery_method is not None:
            if self.delivery_method not in ["email", "download"]:
                raise ValueError("delivery_method must be either 'email' or 'download'")

            if self.delivery_method == "email":
                if not self.email or not self.email.strip():
                    raise ValueError(
                        "email is required when delivery_method is 'email'"
                    )
                # Validate email format using Pydantic's EmailStr
                try:
                    # Use field_validator approach - validate email format
                    import re

                    email_pattern = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
                    if not re.match(email_pattern, self.email.strip()):
                        raise ValueError("Invalid email address format")
                except Exception as e:
                    raise ValueError(f"Invalid email address: {str(e)}")

        return self

    model_config = ConfigDict(
        extra="forbid",  # Reject unknown question sets
        populate_by_name=True,  # Allow both kebab-case and snake_case
    )
