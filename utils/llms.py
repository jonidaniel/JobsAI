import os
import logging

from dotenv import load_dotenv

from openai import OpenAI

logger = logging.getLogger(__name__)

load_dotenv()
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_MODEL:
    logger.warning(
        " OPENAI_MODEL not found in environment. OpenAI calls will fail without it."
    )
if not OPENAI_API_KEY:
    logger.warning(
        " OPENAI_API_KEY not found in environment. OpenAI calls will fail without it."
    )

client = OpenAI(api_key=OPENAI_API_KEY)


def call_llm(system_prompt: str, user_prompt: str, max_tokens: int = 800) -> str:
    """
    Call an LLM.

    Args:
        user_prompt: user prompt
        system_prompt: system prompt
        max_tokens: maximum amount of tokens reserved for the call

    Returns:
        text: the complete LLM response text
    """

    # Get response from LLM
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
        temperature=0.2,
    )

    text = response.choices[0].message.content

    logger.debug(" LLM response: %s", text[:500])

    return text
