"""
Request Schemas for Frontend Payload Validation.

This module defines Pydantic models for validating and transforming frontend form data.
It handles the conversion between frontend kebab-case keys and backend snake_case,
and validates data types and constraints.

Key Models:
    - FrontendPayload: Main model for validating complete form submissions
    - GeneralQuestionItem: Validates general questions (job level, boards, etc.)
    - TechnologySetItem: Validates technology experience levels (sliders)
    - AdditionalInfoItem: Validates personal description field

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
)

from jobsai.config.validation_constants import (
    VALID_GENERAL_KEYS,
    VALID_JOB_LEVELS,
    VALID_JOB_BOARDS,
    VALID_DEEP_MODE,
    VALID_COVER_LETTER_NUM_RANGE,
    VALID_COVER_LETTER_STYLE,
)


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
