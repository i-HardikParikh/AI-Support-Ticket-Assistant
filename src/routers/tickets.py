"""
routers/tickets.py — All ticket-related API endpoints.

Endpoints:
  POST /tickets/analyze       → analyze a new ticket (main AI endpoint)
  GET  /tickets               → list all tickets (with optional status filter)
  GET  /tickets/{id}          → get a single ticket by ID
  POST /tickets/feedback      → agent submits feedback on a ticket
  GET  /tickets/stats         → dashboard statistics
  POST /tickets/webhook/email → inbound email webhook (Postmark / SendGrid)
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from src.db.database import (
    get_dashboard_stats,
    get_ticket_by_id,
    get_tickets,
    save_feedback,
    save_ticket,
)
from src.models import (
    DashboardStats,
    FeedbackRequest,
    FeedbackResponse,
    TicketRequest,
    TicketResponse,
    TicketStatus,
)
from src.services.llm_service import LLMError
from src.services.ticket_analyzer import analyze_ticket

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tickets", tags=["Tickets"])


# ── Analyze a ticket ───────────────────────────────────────────────────────────

@router.post("/analyze", response_model=TicketResponse, summary="Analyze a support ticket")
async def analyze_ticket_endpoint(request: TicketRequest) -> TicketResponse:
    """
    Main endpoint. Accepts a ticket, runs AI analysis, saves to DB.

    curl example:
        curl -X POST http://localhost:8000/tickets/analyze \\
             -H "Content-Type: application/json" \\
             -d '{"ticket": "I was charged twice this month."}'
    """
    ticket_text = request.ticket.strip()
    if not ticket_text:
        raise HTTPException(status_code=422, detail="Ticket text cannot be empty.")

    logger.info("Analyzing ticket from %s: %s…", request.source, ticket_text[:80])

    try:
        result = await analyze_ticket(ticket_text)
    except LLMError as exc:
        logger.error("LLM failure: %s", exc)
        # Save the failed ticket so it's not lost
        ticket_id = await save_ticket(
            raw_text=ticket_text,
            category="other",
            draft_reply="",
            escalation=True,
            reason="AI processing failed — needs manual handling.",
            confidence=0.0,
            sender_email=request.sender_email,
            sender_name=request.sender_name,
            source=request.source or "api",
        )
        raise HTTPException(
            status_code=503,
            detail=f"AI unavailable. Ticket saved with ID {ticket_id} for manual review.",
        )

    # Save to DB
    ticket_id = await save_ticket(
        raw_text=ticket_text,
        category=result.category.value,
        draft_reply=result.draft_reply,
        escalation=result.escalation,
        reason=result.reason,
        confidence=result.confidence,
        sender_email=request.sender_email,
        sender_name=request.sender_name,
        source=request.source or "api",
    )

    result.id = ticket_id
    result.status = TicketStatus.ESCALATED if result.escalation else TicketStatus.PENDING
    return result


# ── List tickets ───────────────────────────────────────────────────────────────

@router.get("/", summary="List all tickets")
async def list_tickets(
    status: Optional[str] = Query(None, description="Filter by status: pending, resolved, escalated, ai_failed"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[dict]:
    return await get_tickets(status=status, limit=limit, offset=offset)


# ── Get single ticket ──────────────────────────────────────────────────────────

@router.get("/stats", response_model=DashboardStats, summary="Dashboard statistics")
async def dashboard_stats() -> DashboardStats:
    """Stats for the agent dashboard — totals, accuracy, category breakdown."""
    data = await get_dashboard_stats()
    return DashboardStats(**data)


@router.get("/{ticket_id}", summary="Get a single ticket")
async def get_ticket(ticket_id: str) -> dict:
    ticket = await get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    return ticket


# ── Agent feedback ─────────────────────────────────────────────────────────────

@router.post("/feedback", response_model=FeedbackResponse, summary="Submit agent feedback")
async def submit_feedback(request: FeedbackRequest) -> FeedbackResponse:
    """
    Agent tells us what they did with the ticket.
    This is the training signal that improves the system over time.

    Actions:
      approved  → agent sent the draft reply as-is (AI was correct)
      edited    → agent changed the reply (AI draft was close but not perfect)
      escalated → agent manually escalated (AI missed it)
      dismissed → agent closed the ticket without replying
    """
    if not request.ticket_id:
        raise HTTPException(status_code=422, detail="ticket_id is required.")

    success = await save_feedback(
        ticket_id=request.ticket_id,
        action=request.action.value,
        corrected_category=request.corrected_category.value if request.corrected_category else None,
        edited_reply=request.edited_reply,
        agent_note=request.agent_note,
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to save feedback.")

    return FeedbackResponse(success=True, message=f"Feedback recorded: {request.action.value}")


# ── Inbound email webhook ──────────────────────────────────────────────────────

@router.post("/webhook/email", summary="Inbound email webhook (Postmark / SendGrid)")
async def email_webhook(payload: dict) -> dict:
    """
    Receives inbound emails from Postmark or SendGrid.
    Automatically extracts the ticket text and runs analysis.

    Configure your email provider to POST inbound emails to:
        POST /tickets/webhook/email

    Postmark inbound payload uses: TextBody, From, FromName
    SendGrid inbound payload uses: text, from
    """
    # Support both Postmark and SendGrid payload formats
    ticket_text = (
        payload.get("TextBody")        # Postmark
        or payload.get("text")         # SendGrid
        or payload.get("body", "")     # generic
    ).strip()

    sender_email = (
        payload.get("From")            # Postmark
        or payload.get("from")         # SendGrid
    )

    sender_name = payload.get("FromName") or payload.get("from_name")

    if not ticket_text:
        logger.warning("Empty email body received on webhook.")
        return {"status": "ignored", "reason": "empty body"}

    logger.info("Email webhook received from %s", sender_email)

    # Reuse the same analyze logic
    fake_request = TicketRequest(
        ticket=ticket_text,
        sender_email=sender_email,
        sender_name=sender_name,
        source="email",
    )
    result = await analyze_ticket_endpoint(fake_request)
    return {"status": "processed", "ticket_id": result.id, "category": result.category}

    