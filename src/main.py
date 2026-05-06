"""
main.py — FastAPI application entry point (production version).

Run with:
    uvicorn src.main:app --reload

Frontend runs on http://localhost:3000 and calls this backend.
"""

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.routers.tickets import router as tickets_router

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Support Ticket Assistant",
    description="Production-grade AI support assistant with agent dashboard, feedback loop, and email webhook.",
    version="2.0.0",
)

# ── CORS — allow the Next.js frontend to call this backend ────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",                    # local dev
        os.getenv("FRONTEND_URL", ""),              # production frontend URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(tickets_router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check() -> dict:
    return {
        "status": "ok",
        "version": "2.0.0",
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
        "groq_configured": bool(os.getenv("GROQ_API_KEY")),
        "supabase_configured": bool(os.getenv("SUPABASE_URL")),
    }


# ── Global error handler ──────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    logger.exception("Unhandled exception.")
    return JSONResponse(status_code=500, content={"detail": str(exc)})

    