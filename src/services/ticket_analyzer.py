"""
services/ticket_analyzer.py — Orchestrates the full ticket analysis pipeline.

Steps:
  1. Load sample tickets from JSON (light RAG knowledge base).
  2. Find 2–3 similar tickets via keyword-based similarity.
  3. Build the prompt (few-shot examples injected).
  4. Call the LLM (Gemini → Groq fallback).
  5. Parse, validate, and return a TicketResponse.
"""

import json
import logging
import os
import re
from pathlib import Path

from src.models import LLMTicketAnalysis, TicketCategory, TicketResponse
from src.services.llm_service import LLMError, call_llm
from src.utils.prompt_templates import build_user_prompt

logger = logging.getLogger(__name__)

# ── Path to the sample tickets knowledge base ──────────────────────────────────
_KB_PATH = Path(__file__).parent.parent / "data" / "sample_tickets.json"


def _load_knowledge_base() -> list[dict]:
    """Load sample tickets from disk. Returns an empty list on failure."""
    try:
        with open(_KB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.warning("Could not load knowledge base: %s", exc)
        return []


def _tokenise(text: str) -> set[str]:
    """Lowercase, strip punctuation, return word set."""
    return set(re.findall(r"[a-z]+", text.lower()))


def _find_similar_tickets(ticket_text: str, kb: list[dict], top_k: int = 3) -> list[dict]:
    """
    Keyword-based (Jaccard-like) similarity search.
    Returns top_k most similar tickets as {'ticket': ..., 'resolution': ...} dicts.
    """
    query_tokens = _tokenise(ticket_text)

    scored: list[tuple[float, dict]] = []

    for entry in kb:
        # Combine the stored ticket text and its keywords for matching
        candidate_tokens = _tokenise(entry.get("ticket", "")) | set(
            entry.get("keywords", [])
        )
        if not candidate_tokens:
            continue

        intersection = query_tokens & candidate_tokens
        union        = query_tokens | candidate_tokens
        score        = len(intersection) / len(union) if union else 0.0

        if score > 0:
            scored.append((score, entry))

    # Sort by score descending, take top_k
    scored.sort(key=lambda x: x[0], reverse=True)

    return [
        {"ticket": e["ticket"], "resolution": e["resolution"]}
        for _, e in scored[:top_k]
    ]


def _normalise_category(raw: str) -> TicketCategory:
    """Map LLM's raw category string to a TicketCategory enum value."""
    mapping = {
        "billing":         TicketCategory.BILLING,
        "bug report":      TicketCategory.BUG_REPORT,
        "bug":             TicketCategory.BUG_REPORT,
        "feature request": TicketCategory.FEATURE_REQUEST,
        "feature":         TicketCategory.FEATURE_REQUEST,
        "account issue":   TicketCategory.ACCOUNT_ISSUE,
        "account":         TicketCategory.ACCOUNT_ISSUE,
        "other":           TicketCategory.OTHER,
    }
    return mapping.get(raw.strip().lower(), TicketCategory.OTHER)


async def analyze_ticket(ticket_text: str) -> TicketResponse:
    """
    Main entry point — analyses a support ticket end-to-end.

    Args:
        ticket_text: Raw ticket string submitted by the customer.

    Returns:
        TicketResponse with category, draft_reply, escalation, reason, confidence.

    Raises:
        LLMError: If all LLM providers fail.
        ValueError: If the LLM returns an unexpected structure.
    """
    # ── Retrieve API keys from environment ────────────────────────────────────
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    groq_key   = os.getenv("GROQ_API_KEY", "")

    # ── Light RAG: find similar tickets ───────────────────────────────────────
    kb = _load_knowledge_base()
    similar = _find_similar_tickets(ticket_text, kb, top_k=3)
    logger.info("Found %d similar tickets for context.", len(similar))

    # ── Build the prompt ──────────────────────────────────────────────────────
    user_prompt = build_user_prompt(ticket_text, similar)

    # ── Call the LLM ──────────────────────────────────────────────────────────
    raw_dict = await call_llm(
        user_prompt=user_prompt,
        gemini_api_key=gemini_key,
        groq_api_key=groq_key,
    )

    # ── Validate with Pydantic ────────────────────────────────────────────────
    analysis = LLMTicketAnalysis(**raw_dict)

    # ── Build and return the final response ───────────────────────────────────
    return TicketResponse(
        category=_normalise_category(analysis.category),
        draft_reply=analysis.draft_reply,
        escalation=analysis.escalation,
        reason=analysis.reason,
        confidence=max(0.0, min(1.0, analysis.confidence)),  # clamp to [0,1]
    )