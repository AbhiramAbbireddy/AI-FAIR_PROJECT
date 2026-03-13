"""
Full analysis endpoint — the main "upload resume, get everything" route.
Also individual endpoints for fairness, trends, skill gaps.
"""
from __future__ import annotations

import os
import tempfile

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from src.config.settings import JOBS_PARSED_PATH
from src.fairness.detector import evaluate_fairness
from src.forecasting.trend_forecaster import compute_current_demand, get_skill_trends
from src.job_pipeline.collector import load_static_jobs
from src.matching.semantic_matcher import match_resume_to_jobs
from src.models.schemas import (
    ExtractedSkill,
    FairnessReport,
    ResumeAnalysisResponse,
    SkillGap,
    SkillTrend,
)
from src.role_mapping.matcher import match_roles
from src.skill_extraction.extractor import extract_skills, extract_text
from src.skill_gap.ranker import rank_skill_gaps

router = APIRouter(prefix="/analysis", tags=["Analysis"])

# ── Helpers ────────────────────────────────────────────────────────────

_jobs_df_cache = None


def _get_jobs_df() -> pd.DataFrame:
    global _jobs_df_cache
    if _jobs_df_cache is None and os.path.exists(JOBS_PARSED_PATH):
        _jobs_df_cache = pd.read_csv(JOBS_PARSED_PATH, nrows=5000)
    if _jobs_df_cache is None:
        _jobs_df_cache = pd.DataFrame()
    return _jobs_df_cache


_postings_cache = None


def _get_postings():
    global _postings_cache
    if _postings_cache is None:
        _postings_cache = load_static_jobs(max_rows=5000)
    return _postings_cache


def _extract_resume(file_bytes: bytes, filename: str) -> str:
    ext = os.path.splitext(filename)[-1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext or ".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        return extract_text(tmp_path, filename=filename)
    finally:
        os.unlink(tmp_path)


# ── Full analysis ─────────────────────────────────────────────────────


@router.post("/full", response_model=ResumeAnalysisResponse)
async def full_analysis(
    file: UploadFile = File(...),
    top_n: int = Form(20),
    min_score: float = Form(0),
    remote_only: bool = Form(False),
    use_ner: bool = Form(True),
):
    """
    One-shot endpoint: upload resume → skills + matches + gaps + trends + fairness.
    """
    content = await file.read()
    text = _extract_resume(content, file.filename or "resume.pdf")

    if not text or len(text.strip()) < 30:
        raise HTTPException(400, "Could not extract meaningful text from the uploaded file.")

    # 1. Skill extraction
    skills = extract_skills(text, use_ner=use_ner)
    skill_names = [s.canonical for s in skills]

    # 2. Role mapping
    role_matches = match_roles(skill_names, min_score=0, top_n=top_n)

    # 3. Job matching (static fallback)
    postings = _get_postings()
    if remote_only:
        postings = [p for p in postings if p.remote]
    matches = match_resume_to_jobs(text, skill_names, postings, top_n=top_n, min_score=min_score)

    # 3. Skill gaps
    jobs_df = _get_jobs_df()
    gaps = rank_skill_gaps(skill_names, jobs_df, top_n=15) if not jobs_df.empty else []

    # 4. Trends
    trends = get_skill_trends(jobs_df) if not jobs_df.empty else []

    # 5. Fairness
    fairness = evaluate_fairness(text)

    return ResumeAnalysisResponse(
        skills=skills,
        matches=matches,
        skill_gaps=gaps,
        trends=trends,
        fairness=fairness,
    )


# ── Individual endpoints ──────────────────────────────────────────────


@router.post("/fairness", response_model=FairnessReport)
async def fairness_check(
    file: UploadFile = File(...),
):
    """Upload resume → fairness analysis only."""
    content = await file.read()
    text = _extract_resume(content, file.filename or "resume.pdf")
    return evaluate_fairness(text)


@router.get("/trends", response_model=list[SkillTrend])
async def skill_trends():
    """Current market skill trends derived from job data."""
    jobs_df = _get_jobs_df()
    if jobs_df.empty:
        return []
    return get_skill_trends(jobs_df)


@router.post("/skill-gaps", response_model=list[SkillGap])
async def skill_gaps(
    file: UploadFile = File(...),
    use_ner: bool = Form(True),
):
    """Upload resume → skill gap analysis."""
    content = await file.read()
    text = _extract_resume(content, file.filename or "resume.pdf")
    skills = extract_skills(text, use_ner=use_ner)
    skill_names = [s.canonical for s in skills]
    jobs_df = _get_jobs_df()
    if jobs_df.empty:
        return []
    return rank_skill_gaps(skill_names, jobs_df, top_n=15)


@router.post("/roles")
async def role_mapping(
    file: UploadFile = File(...),
    use_ner: bool = Form(True),
    top_n: int = Form(10),
    min_score: float = Form(10),
):
    """Upload resume → suitable job role suggestions."""
    content = await file.read()
    text = _extract_resume(content, file.filename or "resume.pdf")
    skills = extract_skills(text, use_ner=use_ner)
    skill_names = [s.canonical for s in skills]
    roles = match_roles(skill_names, min_score=min_score, top_n=top_n)
    return [
        {
            "role": r.role,
            "domain": r.domain,
            "description": r.description,
            "score": r.score,
            "core_match_pct": r.core_match_pct,
            "matched_core": r.matched_core,
            "matched_optional": r.matched_optional,
            "missing_core": r.missing_core,
            "total_matched": r.total_matched,
        }
        for r in roles
    ]
