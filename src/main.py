"""
main.py — FastAPI application entry point.

Run with:
    uvicorn src.main:app --reload

Example curl request:
    curl -X POST http://localhost:8000/analyze-ticket \
         -H "Content-Type: application/json" \
         -d '{"ticket": "I was double-charged this month and need a refund immediately."}'

Expected JSON response:
    {
        "category": "billing",
        "draft_reply": "Thank you for reaching out. We sincerely apologise for the inconvenience...",
        "escalation": false,
        "reason": "Standard billing dispute — no signs of SLA breach or excessive amount.",
        "confidence": 0.92
    }
"""

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from src.models import TicketRequest, TicketResponse
from src.services.llm_service import LLMError
from src.services.ticket_analyzer import analyze_ticket

# ── Load .env before anything else ────────────────────────────────────────────
load_dotenv()

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── FastAPI app ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Support Ticket Assistant",
    description=(
        "Classifies B2B SaaS support tickets, drafts professional replies, "
        "and flags escalations — powered by Gemini with Groq fallback."
    ),
    version="1.0.0",
)


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check() -> dict:
    """Quick liveness probe."""
    return {"status": "ok"}


# ── Main endpoint ──────────────────────────────────────────────────────────────
@app.post(
    "/analyze-ticket",
    response_model=TicketResponse,
    tags=["Tickets"],
    summary="Analyse a support ticket",
)
async def analyze_ticket_endpoint(request: TicketRequest) -> TicketResponse:
    """
    Accepts a raw support ticket and returns:
    - **category**    – one of billing / bug report / feature request / account issue / other
    - **draft_reply** – a professional reply ready for the agent to review
    - **escalation**  – whether a senior agent should take over
    - **reason**      – why escalation was/wasn't triggered
    - **confidence**  – model's certainty (0.0 – 1.0)
    """
    ticket_text = request.ticket.strip()

    # Guard: reject trivially empty input even after stripping
    if not ticket_text:
        raise HTTPException(status_code=422, detail="Ticket text must not be empty.")

    logger.info("Received ticket (%d chars): %s…", len(ticket_text), ticket_text[:80])

    try:
        result = await analyze_ticket(ticket_text)
    except LLMError as exc:
        logger.error("LLM failure: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=f"AI service unavailable: {exc}",
        )
    except Exception as exc:
        logger.exception("Unexpected error while analysing ticket.")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {exc}",
        )

    logger.info(
        "Result → category=%s | escalation=%s | confidence=%.2f",
        result.category,
        result.escalation,
        result.confidence,
    )
    return result


# ── Global error handler ───────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):  # type: ignore[type-arg]
    logger.exception("Unhandled exception.")
    return JSONResponse(status_code=500, content={"detail": str(exc)})