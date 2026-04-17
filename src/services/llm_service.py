"""
services/llm_service.py — LLM integration layer.

Primary:  Google Gemini (gemini-1.5-flash)
Fallback: Groq          (llama3-8b-8192 / mixtral-8x7b-32768)

Retry logic is handled by `tenacity`:
  - Up to 3 attempts on the primary provider.
  - If all retries fail, automatically switch to the fallback provider.
"""

import json
import logging
import os
from typing import Any

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from src.utils.prompt_templates import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


# ── Gemini ─────────────────────────────────────────────────────────────────────

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


class LLMError(Exception):
    """Raised when all LLM providers fail."""


def _extract_error_detail(response: httpx.Response) -> str:
    """Return a compact provider error message for logs/exceptions."""
    try:
        payload = response.json()
        detail = payload.get("error", payload)
        return str(detail)
    except Exception:
        text = response.text.strip()
        return text[:500] if text else "<no response body>"


def _is_retryable_exception(exc: Exception) -> bool:
    """Retry only transient failures, not permanent 4xx validation/auth issues."""
    if isinstance(exc, (httpx.TimeoutException, httpx.RequestError)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in {408, 429, 500, 502, 503, 504}
    return False


# ── Gemini call ────────────────────────────────────────────────────────────────

@retry(
    retry=retry_if_exception(_is_retryable_exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
async def _call_gemini(api_key: str, user_prompt: str) -> str:
    """
    Send a request to the Gemini API and return the raw text response.
    Retries up to 3 times with exponential back-off on network/HTTP errors.
    """
    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.2,         # low temp → deterministic, structured output
            "maxOutputTokens": 512,
            "responseMimeType": "application/json",  # Gemini native JSON mode
        },
    }

    gemini_api_url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            gemini_api_url,
            headers={"x-goog-api-key": api_key},
            json=payload,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = _extract_error_detail(exc.response)
            raise LLMError(
                f"Gemini request failed ({exc.response.status_code}): {detail}"
            ) from exc

    data = response.json()
    # Extract text from Gemini's nested response structure
    return data["candidates"][0]["content"]["parts"][0]["text"]


# ── Groq call ──────────────────────────────────────────────────────────────────

@retry(
    retry=retry_if_exception(_is_retryable_exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
async def _call_groq(api_key: str, user_prompt: str) -> str:
    """
    Send a request to the Groq API (OpenAI-compatible) and return raw text.
    Retries up to 3 times with exponential back-off.
    """
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 512,
        "response_format": {"type": "json_object"},  # Groq JSON mode
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            GROQ_API_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = _extract_error_detail(exc.response)
            raise LLMError(
                f"Groq request failed ({exc.response.status_code}): {detail}"
            ) from exc

    data = response.json()
    return data["choices"][0]["message"]["content"]


# ── Public interface ───────────────────────────────────────────────────────────

async def call_llm(
    user_prompt: str,
    gemini_api_key: str,
    groq_api_key: str,
) -> dict[str, Any]:
    """
    Try Gemini first; fall back to Groq if Gemini fails after all retries.
    Returns a parsed dict (never raw text) so callers stay clean.
    """
    raw_text: str | None = None

    # ── 1. Try Gemini ──────────────────────────────────────────────────────────
    if gemini_api_key and gemini_api_key != "your_gemini_api_key_here":
        try:
            logger.info("Calling Gemini API…")
            raw_text = await _call_gemini(gemini_api_key, user_prompt)
            logger.info("Gemini response received.")
        except Exception as exc:
            logger.warning("Gemini failed (%s). Falling back to Groq.", exc)

    # ── 2. Fall back to Groq ───────────────────────────────────────────────────
    if raw_text is None:
        if not groq_api_key or groq_api_key == "your_groq_api_key_here":
            raise LLMError(
                "Both Gemini and Groq API keys are missing or invalid. "
                "Please set them in the .env file."
            )
        try:
            logger.info("Calling Groq API…")
            raw_text = await _call_groq(groq_api_key, user_prompt)
            logger.info("Groq response received.")
        except Exception as exc:
            raise LLMError(f"All LLM providers failed. Last error: {exc}") from exc

    # ── 3. Parse JSON safely ───────────────────────────────────────────────────
    try:
        # Strip accidental markdown fences some models still emit
        cleaned = raw_text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse LLM JSON response: %s", raw_text)
        raise LLMError(f"LLM returned invalid JSON: {exc}") from exc