"""
Job matching & search endpoints.
"""
from __future__ import annotations

import os
import tempfile
from typing import Optional

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from src.config.settings import JOBS_PARSED_PATH
from src.job_pipeline.collector import JobCollector, load_static_jobs
from src.matching.semantic_matcher import (
    jobs_df_to_postings,
    match_resume_to_jobs,
)
from src.models.schemas import MatchResult
from src.skill_extraction.extractor import extract_skill_names, extract_text

router = APIRouter(prefix="/jobs", tags=["Jobs"])

# Lazy cache
_cached_postings = None


def _get_postings():
    global _cached_postings
    if _cached_postings is None:
        _cached_postings = load_static_jobs(max_rows=5000)
    return _cached_postings


@router.post("/match", response_model=list[MatchResult])
async def match_jobs(
    file: UploadFile = File(...),
    top_n: int = Form(20),
    min_score: float = Form(0),
    remote_only: bool = Form(False),
):
    """Upload resume → get ranked job matches with SHAP explanations."""
    ext = os.path.splitext(file.filename or "")[-1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext or ".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        text = extract_text(tmp_path, filename=file.filename or "")
        skills = extract_skill_names(text, use_ner=True)
        postings = _get_postings()
        if remote_only:
            postings = [p for p in postings if p.remote]
        results = match_resume_to_jobs(text, skills, postings, top_n=top_n, min_score=min_score)
        return results
    finally:
        os.unlink(tmp_path)


@router.get("/search")
async def search_live_jobs(
    query: str = Query("software engineer"),
    location: str = Query(""),
    max_results: int = Query(20),
    remote_only: bool = Query(False),
):
    """Search live job APIs (JSearch / Adzuna) or fallback to static data."""
    collector = JobCollector()
    jobs = collector.search(query=query, location=location, max_results=max_results, remote_only=remote_only)
    return {"jobs": jobs, "count": len(jobs), "source": jobs[0].source if jobs else "none"}
