"""
models.py — All Pydantic models for the entire application.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────────────

class TicketCategory(str, Enum):
    BILLING = "billing"
    BUG_REPORT = "bug report"
    FEATURE_REQUEST = "feature request"
    ACCOUNT_ISSUE = "account issue"
    OTHER = "other"


class AgentAction(str, Enum):
    APPROVED = "approved"
    EDITED = "edited"
    ESCALATED = "escalated"
    DISMISSED = "dismissed"


class TicketStatus(str, Enum):
    PENDING = "pending"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    AI_FAILED = "ai_failed"


# ── API Request ────────────────────────────────────────────────────────────────

class TicketRequest(BaseModel):
    ticket: str = Field(..., min_length=1, max_length=5000)
    sender_email: Optional[str] = Field(None)
    sender_name: Optional[str] = Field(None)
    source: Optional[str] = Field("api")


# ── AI Analysis Response ───────────────────────────────────────────────────────

class TicketResponse(BaseModel):
    id: Optional[str] = Field(None)
    category: TicketCategory
    draft_reply: str
    escalation: bool
    reason: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    status: TicketStatus = TicketStatus.PENDING


# ── Internal LLM parse model ───────────────────────────────────────────────────

class LLMTicketAnalysis(BaseModel):
    category: str
    draft_reply: str
    escalation: bool
    reason: str
    confidence: float


# ── Feedback from agent ────────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    ticket_id: str
    action: AgentAction
    corrected_category: Optional[TicketCategory] = None
    edited_reply: Optional[str] = None
    agent_note: Optional[str] = None


class FeedbackResponse(BaseModel):
    success: bool
    message: str


# ── Full ticket record returned from DB ───────────────────────────────────────

class TicketRecord(BaseModel):
    id: str
    raw_text: str
    sender_email: Optional[str]
    sender_name: Optional[str]
    source: str
    category: str
    draft_reply: str
    escalation: bool
    reason: str
    confidence: float
    status: str
    agent_action: Optional[str]
    corrected_category: Optional[str]
    edited_reply: Optional[str]
    agent_note: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]


# ── Dashboard stats ────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_tickets: int
    pending: int
    resolved: int
    escalated: int
    ai_failed: int
    accuracy_rate: float
    escalation_rate: float
    avg_confidence: float
    category_breakdown: dict
    recent_overrides: int

    