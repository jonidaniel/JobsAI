"""
JobsAI/src/jobsai/utils/llms.py

Functions related to LLM use.

    call_llm
    extract_json
"""

import os
import logging
import json
from typing import Optional

from dotenv import load_dotenv

from openai import OpenAI

logger = logging.getLogger(__name__)

load_dotenv()
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validate required environment variables
if not OPENAI_MODEL:
    error_msg = "OPENAI_MODEL not found in environment variables. Please set OPENAI_MODEL in your .env file or environment."
    logger.error(error_msg)
    raise ValueError(error_msg)

if not OPENAI_API_KEY:
    error_msg = "OPENAI_API_KEY not found in environment variables. Please set OPENAI_API_KEY in your .env file or environment."
    logger.error(error_msg)
    raise ValueError(error_msg)

# Initialize OpenAI client with validated API key
# This will raise an error immediately if the API key is invalid format
try:
    client = OpenAI(api_key=OPENAI_API_KEY)
except Exception as e:
    error_msg = f"Failed to initialize OpenAI client: {str(e)}"
    logger.error(error_msg)
    raise ValueError(error_msg) from e


def call_llm(system_prompt: str, user_prompt: str, max_tokens: int = 800) -> str:
    """
    Call OpenAI LLM API with system and user prompts.

    This is the central function for all LLM interactions in the JobsAI system.
    It's used by:
    - ProfilerAgent: To extract skill profiles from form submissions
    - ReporterAgent: To generate cover letter instructions
    - GeneratorAgent: To write cover letter content

    Args:
        system_prompt (str): System prompt defining the LLM's role and behavior
        user_prompt (str): User prompt containing the actual task/input
        max_tokens (int): Maximum number of tokens in the response (default: 800)

    Returns:
        str: The complete LLM response text

    Raises:
        Exception: If OpenAI API call fails (handled by caller)
    """

    # Make API call to OpenAI
    # Temperature is set low (0.2) for more deterministic, focused responses
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
        temperature=0.2,  # Low temperature for consistent, focused output
    )

    # Validate response structure
    if not response or not hasattr(response, "choices"):
        error_msg = (
            "Invalid response structure from OpenAI API: missing 'choices' attribute"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    if not response.choices or len(response.choices) == 0:
        error_msg = "OpenAI API returned empty choices array"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Extract text content from response
    message = response.choices[0].message
    if not message or not hasattr(message, "content"):
        error_msg = (
            "Invalid response structure from OpenAI API: missing 'content' attribute"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    text = message.content

    # Check if content is None (can happen with some API responses)
    if text is None:
        error_msg = "OpenAI API returned None content in response"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Log first 500 characters for debugging (full response may be very long)
    logger.debug(" LLM response: %s", text[:500])

    return text


def extract_json(text: str) -> Optional[str]:
    """
    Extract JSON substring from raw LLM response text.

    LLMs often return JSON wrapped in markdown code blocks or with extra text.
    This function finds and extracts just the JSON portion by:
    1. Finding the first opening brace '{'
    2. Balancing braces to find the matching closing brace '}'
    3. Extracting the substring between them

    Args:
        text (str): The raw LLM response text (may contain markdown, explanations, etc.)

    Returns:
        Optional[str]:
            - The extracted JSON string if valid JSON is found
            - None if no valid JSON can be extracted

    Example:
        Input: "Here is the profile: ```json\n{\"name\": \"John\"}\n```"
        Output: '{"name": "John"}'
    """

    # Find where the JSON object starts (first opening brace)
    start = text.find("{")

    # If no opening brace found, there's no JSON
    if start == -1:
        return None

    # Balance braces to find the matching closing brace
    # This handles nested objects correctly
    brace = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            brace += 1
        elif text[i] == "}":
            brace -= 1
            # When braces are balanced, we've found the complete JSON object
            if brace == 0:
                return text[start : i + 1]

    # Fallback: if brace balancing didn't work, try parsing the entire text
    # This handles cases where the text is already valid JSON
    try:
        json.loads(text)
        return text
    except Exception:
        return None
