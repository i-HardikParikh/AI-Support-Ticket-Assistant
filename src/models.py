"""
models.py — Pydantic data models for request/response validation.
"""

from enum import Enum
from pydantic import BaseModel, Field


# ── Ticket categories ──────────────────────────────────────────────────────────

class TicketCategory(str, Enum):
    BILLING = "billing"
    BUG_REPORT = "bug report"
    FEATURE_REQUEST = "feature request"
    ACCOUNT_ISSUE = "account issue"
    OTHER = "other"


# ── API request ────────────────────────────────────────────────────────────────

class TicketRequest(BaseModel):
    ticket: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The raw support ticket text submitted by the user.",
    )


# ── API response ───────────────────────────────────────────────────────────────

class TicketResponse(BaseModel):
    category: TicketCategory
    draft_reply: str = Field(..., description="Professional draft reply for the agent to review/send.")
    escalation: bool = Field(..., description="Whether this ticket should be escalated to a senior agent.")
    reason: str = Field(..., description="Clear explanation of the escalation decision.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model's confidence score (0.0 – 1.0).")


# ── Internal LLM parse model (raw JSON from LLM) ─────────────────────────────

class LLMTicketAnalysis(BaseModel):
    """
    Mirrors TicketResponse but uses plain str for category
    so we can coerce the LLM's raw string before creating TicketResponse.
    """
    category: str
    draft_reply: str
    escalation: bool
    reason: str
    confidence: float