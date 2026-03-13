"""
FAIR-PATH — FastAPI Backend
============================
Serves the ML service layer with endpoints for:
    - Resume skill extraction
    - Semantic job matching
    - SHAP explainability
    - Skill gap analysis
    - Trend forecasting
    - Fairness detection
    - Live job search

Run:
    uvicorn src.api.app:app --reload --port 8000
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import jobs, resume, analysis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load heavy resources once on startup."""
    # Warm up the skill vocabulary (fast)
    from src.skill_extraction.extractor import _get_skill_vocab
    _get_skill_vocab()
    yield


app = FastAPI(
    title="FAIR-PATH API",
    description="AI-Powered Career Intelligence Platform",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ──────────────────────────────────────────────────
app.include_router(resume.router)
app.include_router(jobs.router)
app.include_router(analysis.router)


@app.get("/")
async def root():
    return {
        "name": "FAIR-PATH API",
        "version": "2.0.0",
        "docs": "/docs",
        "endpoints": [
            "/resume/extract-skills",
            "/resume/parse-text",
            "/jobs/match",
            "/jobs/search",
            "/analysis/full",
            "/analysis/fairness",
            "/analysis/trends",
            "/analysis/skill-gaps",
        ],
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
