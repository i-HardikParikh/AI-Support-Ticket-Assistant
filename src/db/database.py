"""
db/database.py — All database operations via Supabase.

We use Supabase (PostgreSQL) to store every ticket and agent feedback.
This replaces the static JSON file from the prototype.

Tables needed (run the SQL in supabase_schema.sql to create them):
  - tickets       → every processed ticket
  - feedback      → every agent action on a ticket
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

import httpx

logger = logging.getLogger(__name__)

# Supabase REST API base — reads from env
def _get_supabase_url() -> str:
    return os.getenv("SUPABASE_URL", "").rstrip("/")

def _get_headers() -> dict:
    key = os.getenv("SUPABASE_SERVICE_KEY", "")
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


# ── Save a new ticket after AI analysis ───────────────────────────────────────

async def save_ticket(
    raw_text: str,
    category: str,
    draft_reply: str,
    escalation: bool,
    reason: str,
    confidence: float,
    sender_email: Optional[str] = None,
    sender_name: Optional[str] = None,
    source: str = "api",
) -> Optional[str]:
    """
    Insert a new ticket record into Supabase.
    Returns the ticket ID string, or None if save failed.
    """
    ticket_id = str(uuid4())
    payload = {
        "id": ticket_id,
        "raw_text": raw_text,
        "sender_email": sender_email,
        "sender_name": sender_name,
        "source": source,
        "category": category,
        "draft_reply": draft_reply,
        "escalation": escalation,
        "reason": reason,
        "confidence": confidence,
        "status": "escalated" if escalation else "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{_get_supabase_url()}/rest/v1/tickets",
                headers=_get_headers(),
                json=payload,
            )
            resp.raise_for_status()
        logger.info("Ticket saved: %s", ticket_id)
        return ticket_id
    except Exception as exc:
        # Don't crash the whole request if DB save fails — just log it
        logger.error("Failed to save ticket to DB: %s", exc)
        return None


# ── Save agent feedback on a ticket ───────────────────────────────────────────

async def save_feedback(
    ticket_id: str,
    action: str,
    corrected_category: Optional[str],
    edited_reply: Optional[str],
    agent_note: Optional[str],
) -> bool:
    """
    Insert a feedback row and update the parent ticket's status.
    Returns True on success.
    """
    now = datetime.now(timezone.utc).isoformat()

    # 1. Insert feedback row
    feedback_payload = {
        "id": str(uuid4()),
        "ticket_id": ticket_id,
        "action": action,
        "corrected_category": corrected_category,
        "edited_reply": edited_reply,
        "agent_note": agent_note,
        "created_at": now,
    }

    # 2. Determine new ticket status
    status_map = {
        "approved": "resolved",
        "edited": "resolved",
        "escalated": "escalated",
        "dismissed": "resolved",
    }
    new_status = status_map.get(action, "resolved")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Save feedback
            r1 = await client.post(
                f"{_get_supabase_url()}/rest/v1/feedback",
                headers=_get_headers(),
                json=feedback_payload,
            )
            r1.raise_for_status()

            # Update ticket status + corrected fields
            update_payload: dict = {
                "status": new_status,
                "agent_action": action,
                "resolved_at": now,
            }
            if corrected_category:
                update_payload["corrected_category"] = corrected_category
            if edited_reply:
                update_payload["edited_reply"] = edited_reply
            if agent_note:
                update_payload["agent_note"] = agent_note

            r2 = await client.patch(
                f"{_get_supabase_url()}/rest/v1/tickets?id=eq.{ticket_id}",
                headers=_get_headers(),
                json=update_payload,
            )
            r2.raise_for_status()

        logger.info("Feedback saved for ticket %s | action=%s", ticket_id, action)
        return True
    except Exception as exc:
        logger.error("Failed to save feedback: %s", exc)
        return False


# ── Fetch all tickets (for dashboard list) ────────────────────────────────────

async def get_tickets(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """
    Fetch tickets from DB, newest first.
    Optionally filter by status: pending / resolved / escalated / ai_failed.
    """
    url = f"{_get_supabase_url()}/rest/v1/tickets?order=created_at.desc&limit={limit}&offset={offset}"
    if status:
        url += f"&status=eq.{status}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=_get_headers())
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Failed to fetch tickets: %s", exc)
        return []


# ── Fetch a single ticket by ID ───────────────────────────────────────────────

async def get_ticket_by_id(ticket_id: str) -> Optional[dict]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_get_supabase_url()}/rest/v1/tickets?id=eq.{ticket_id}",
                headers=_get_headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            return data[0] if data else None
    except Exception as exc:
        logger.error("Failed to fetch ticket %s: %s", ticket_id, exc)
        return None


# ── Stats for dashboard ────────────────────────────────────────────────────────

async def get_dashboard_stats() -> dict:
    """
    Compute stats from the tickets table.
    Attempts to use the optimized database view 'dashboard_stats'.
    Falls back to in-memory aggregation if the view is not yet created.
    """
    try:
        # Try fetching from the database-optimized view
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_get_supabase_url()}/rest/v1/dashboard_stats",
                headers=_get_headers(),
            )
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    stats = data[0]
                    # Ensure category breakdown is a valid dict
                    if not isinstance(stats.get("category_breakdown"), dict):
                        stats["category_breakdown"] = {}
                    return stats
    except Exception as exc:
        logger.warning("DB view dashboard_stats not available, falling back: %s", exc)

    # Fallback to in-memory calculation
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_get_supabase_url()}/rest/v1/tickets?select=status,category,confidence,agent_action,corrected_category,created_at",
                headers=_get_headers(),
            )
            resp.raise_for_status()
            tickets = resp.json()

        if not tickets:
            return _empty_stats()

        total = len(tickets)
        pending   = sum(1 for t in tickets if t["status"] == "pending")
        resolved  = sum(1 for t in tickets if t["status"] == "resolved")
        escalated = sum(1 for t in tickets if t["status"] == "escalated")
        ai_failed = sum(1 for t in tickets if t["status"] == "ai_failed")

        # Accuracy = tickets where agent approved without any edit or correction
        approved_asis = sum(1 for t in tickets if t.get("agent_action") == "approved")
        resolved_total = resolved + escalated
        accuracy = round(approved_asis / resolved_total * 100, 1) if resolved_total > 0 else 0.0

        escalation_rate = round(escalated / total * 100, 1) if total > 0 else 0.0

        confidences = [t["confidence"] for t in tickets if t.get("confidence")]
        avg_conf = round(sum(confidences) / len(confidences), 2) if confidences else 0.0

        # Category breakdown
        category_breakdown: dict = {}
        for t in tickets:
            cat = t.get("category", "other")
            category_breakdown[cat] = category_breakdown.get(cat, 0) + 1

        # Overrides in last 7 days
        from datetime import timedelta
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        recent_overrides = sum(
            1 for t in tickets
            if t.get("corrected_category")
            and datetime.fromisoformat(t["created_at"].replace("Z", "+00:00")) > week_ago
        )

        return {
            "total_tickets": total,
            "pending": pending,
            "resolved": resolved,
            "escalated": escalated,
            "ai_failed": ai_failed,
            "accuracy_rate": accuracy,
            "escalation_rate": escalation_rate,
            "avg_confidence": avg_conf,
            "category_breakdown": category_breakdown,
            "recent_overrides": recent_overrides,
        }

    except Exception as exc:
        logger.error("Failed to compute stats in fallback: %s", exc)
        return _empty_stats()


def _empty_stats() -> dict:
    return {
        "total_tickets": 0, "pending": 0, "resolved": 0,
        "escalated": 0, "ai_failed": 0, "accuracy_rate": 0.0,
        "escalation_rate": 0.0, "avg_confidence": 0.0,
        "category_breakdown": {}, "recent_overrides": 0,
    }

    