"""Groq LLM client wrapper for future agent workflows."""

from __future__ import annotations

import os

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "llama-3.3-70b-versatile"


def _get_api_key() -> str:
    """Return the configured Groq API key."""

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not configured")
    return api_key


def query_agent(messages: list[dict[str, str]], temperature: float = 0.2) -> str:
    """Send chat messages to the Groq model and return the assistant response."""

    api_key = _get_api_key()

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=temperature,
        )
        message = response.choices[0].message.content
        return message or ""
    except ImportError:
        import openai

        openai.api_key = api_key
        openai.api_base = GROQ_BASE_URL
        if hasattr(openai, "base_url"):
            openai.base_url = GROQ_BASE_URL
        response = openai.ChatCompletion.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=temperature,
        )
        return response["choices"][0]["message"].get("content", "") or ""
