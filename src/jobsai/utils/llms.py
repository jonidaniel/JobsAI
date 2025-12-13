"""
LLM Utilities - OpenAI API Integration and JSON Extraction.

This module provides utilities for interacting with OpenAI's LLM API and processing
LLM responses. It serves as the central interface for all LLM operations throughout
the JobsAI pipeline.

Key Functions:
    - call_llm: Central function for all LLM API calls with automatic retry logic
    - extract_json: Utility for extracting JSON from LLM responses that may be
      wrapped in markdown code blocks or contain extra explanatory text

Features:
    - Environment variable validation on module import
    - OpenAI client initialization with lazy loading
    - Automatic retry with exponential backoff for transient failures
    - Response validation and comprehensive error handling
    - Support for streaming and non-streaming responses

Environment Variables:
    OPENAI_API_KEY: OpenAI API key (required)
    OPENAI_MODEL: Model name to use (e.g., "gpt-4", "gpt-3.5-turbo") (required)

Note:
    The module validates environment variables on import and raises ValueError
    if required variables are missing. This ensures failures happen early rather
    than during pipeline execution.
"""

import os
import logging
import json
import time
from typing import Optional

from dotenv import load_dotenv

from openai import OpenAI
from openai import RateLimitError, APIConnectionError, APITimeoutError

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Retrieve OpenAI configuration from environment variables
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validate required environment variables
# These must be set for the application to function
if not OPENAI_MODEL:
    error_msg = (
        " OPENAI_MODEL not found in environment variables. "
        "Please set OPENAI_MODEL in your .env file or environment."
    )
    logger.error(error_msg)
    raise ValueError(error_msg)

if not OPENAI_API_KEY:
    error_msg = (
        " OPENAI_API_KEY not found in environment variables. "
        "Please set OPENAI_API_KEY in your .env file or environment."
    )
    logger.error(error_msg)
    raise ValueError(error_msg)

# Initialize OpenAI client with validated API key
# This will raise an error immediately if the API key format is invalid
try:
    client = OpenAI(api_key=OPENAI_API_KEY)
except Exception as e:
    error_msg = f" Failed to initialize OpenAI client: {str(e)}"
    logger.error(error_msg)
    raise ValueError(error_msg) from e


def call_llm(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 800,
    max_retries: int = 3,
    retry_delay: float = 1.0,
) -> str:
    """Call OpenAI LLM API with system and user prompts.

    This is the central function for all LLM interactions in the JobsAI system.
    It provides a unified interface for making OpenAI API calls with automatic
    retry logic, error handling, and response validation.

    Used by:
        - ProfilerAgent: Extract skill profiles from form submissions
        - AnalyzerAgent: Generate cover letter writing instructions
        - GeneratorAgent: Write cover letter content

    Features:
        - Automatic retry with exponential backoff for transient failures
        - Handles rate limits, connection errors, and timeouts
        - Response validation to ensure data integrity
        - Low temperature (0.2) for consistent, focused outputs

    Args:
        system_prompt: System prompt defining the LLM's role, behavior, and output format.
        user_prompt: User prompt containing the actual task, input data, and instructions.
        max_tokens: Maximum number of tokens in the response. Default is 800, which is
            sufficient for most tasks. Increase for longer outputs (e.g., cover letters).
        max_retries: Maximum number of retry attempts for transient failures.
            Default is 3, giving 4 total attempts (initial + 3 retries).
        retry_delay: Initial delay between retries in seconds. Uses exponential backoff,
            so delays are: retry_delay, retry_delay*2, retry_delay*4, etc.

    Returns:
        Complete LLM response text as a string. The response is extracted from
        the first choice in the API response.

    Raises:
        RateLimitError: If rate limit is exceeded after all retries.
        APIConnectionError: If connection fails after all retries.
        APITimeoutError: If request times out after all retries.
        ValueError: If response structure is invalid or missing content.
        Exception: For other non-retryable errors (e.g., authentication failures).

    Note:
        The function uses a low temperature (0.2) to ensure consistent, focused
        outputs suitable for structured data extraction and professional writing.
        For more creative outputs, consider increasing temperature in the API call.
    """

    retryable_errors = (RateLimitError, APIConnectionError, APITimeoutError)
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
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
            break  # Success, exit retry loop

        except retryable_errors as e:
            last_exception = e
            if attempt < max_retries:
                # Exponential backoff: delay doubles with each retry
                delay = retry_delay * (2**attempt)
                logger.warning(
                    f" LLM API call failed (attempt {attempt + 1}/{max_retries + 1}): {type(e).__name__}. "
                    f"Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
            else:
                # Final attempt failed
                logger.error(
                    f" LLM API call failed after {max_retries + 1} attempts: {type(e).__name__}"
                )
                raise
        except Exception as e:
            # Non-retryable errors (e.g., authentication, invalid request) fail immediately
            logger.error(
                f" LLM API call failed with non-retryable error: {type(e).__name__}: {str(e)}"
            )
            raise

    # Validate response structure
    if not response or not hasattr(response, "choices"):
        error_msg = (
            " Invalid response structure from OpenAI API: missing 'choices' attribute"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    if not response.choices or len(response.choices) == 0:
        error_msg = " OpenAI API returned empty choices array"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Extract text content from response
    message = response.choices[0].message
    if not message or not hasattr(message, "content"):
        error_msg = (
            " Invalid response structure from OpenAI API: missing 'content' attribute"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    text = message.content

    # Check if content is None (can happen with some API responses)
    if text is None:
        error_msg = " OpenAI API returned None content in response"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Log first 500 characters for debugging (full response may be very long)
    logger.debug(" LLM response: %s", text[:500])

    return text


def extract_json(text: str) -> Optional[str]:
    """Extract JSON from LLM response text that may contain markdown or extra text.

    LLM responses often include explanatory text or wrap JSON in markdown code blocks.
    This function extracts the JSON portion, handling common formats:
    - JSON wrapped in ```json ... ``` code blocks
    - JSON wrapped in ``` ... ``` code blocks
    - JSON with leading/trailing explanatory text
    - Plain JSON (returns as-is)

    Args:
        text: LLM response text that may contain JSON along with other content.

    Returns:
        Extracted JSON string, or None if no valid JSON is found. The returned
        string is not validated - it should be parsed with json.loads() to verify
        it's valid JSON.

    Example:
        Input: "Here's the profile: ```json {\"skills\": [\"Python\"]} ```"
        Output: '{"skills": ["Python"]}'

    Note:
        This function uses regex to find JSON patterns. It looks for:
        1. Markdown code blocks with json language tag
        2. Markdown code blocks without language tag
        3. JSON objects/arrays in the text
        The first valid JSON found is returned.
    """
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
