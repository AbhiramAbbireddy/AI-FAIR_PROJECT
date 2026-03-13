"""
Semantic Job Matching Engine
============================
Combines three signals:

    score = 0.5 × semantic_similarity
          + 0.3 × skill_overlap
          + 0.2 × experience_relevance

Uses Sentence-BERT (all-MiniLM-L6-v2) for embeddings and cosine similarity.

Optimised for speed:
    - Batch SBERT encoding (all job descriptions in one call)
    - Pre-filter by skill overlap before running SBERT
    - Vectorised cosine similarity via numpy
"""
from __future__ import annotations

import re
from typing import Optional

import numpy as np
import pandas as pd

from src.config.settings import (
    EXPERIENCE_KEYWORDS,
    EXPERIENCE_WEIGHT,
    PREFERRED_SKILL_W,
    REQUIRED_SKILL_W,
    SBERT_MODEL,
    SEMANTIC_WEIGHT,
    SKILL_OVERLAP_WEIGHT,
)
from src.models.schemas import JobPosting, MatchResult, SkillContribution

# ---------------------------------------------------------------------------
# Lazy-loaded Sentence-BERT model
# ---------------------------------------------------------------------------
_sbert_model = None


def _get_sbert():
    global _sbert_model
    if _sbert_model is None:
        try:
            from sentence_transformers import SentenceTransformer

            _sbert_model = SentenceTransformer(SBERT_MODEL)
        except Exception:
            _sbert_model = None
    return _sbert_model


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    a = a.flatten()
    b = b.flatten()
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _batch_cosine_sim(resume_emb: np.ndarray, job_embs: np.ndarray) -> np.ndarray:
    """Vectorised cosine similarity: one resume vs N job embeddings."""
    resume_emb = resume_emb.flatten()
    norms = np.linalg.norm(job_embs, axis=1) * np.linalg.norm(resume_emb)
    norms = np.where(norms == 0, 1.0, norms)
    return np.dot(job_embs, resume_emb) / norms


def _detect_experience_level(text: str) -> str:
    text_lower = text.lower()
    for level, keywords in EXPERIENCE_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return level
    return "unknown"


def _experience_score(resume_text: str, job_exp: str) -> float:
    """
    Return 0-1 score for how well the candidate's experience matches
    the job's stated experience level.
    """
    resume_level = _detect_experience_level(resume_text)
    job_level = job_exp.lower().strip() if job_exp else "unknown"

    levels = {"entry": 0, "mid": 1, "senior": 2, "executive": 3, "unknown": 1}
    r = levels.get(resume_level, 1)
    j_level = "unknown"
    for key in levels:
        if key in job_level:
            j_level = key
            break
    j = levels.get(j_level, 1)

    diff = abs(r - j)
    if diff == 0:
        return 1.0
    if diff == 1:
        return 0.6
    return 0.2


def _skill_overlap(
    resume_skills: set[str],
    required: set[str],
    preferred: set[str],
) -> tuple[float, list[str], list[str], list[str], list[str]]:
    """
    Weighted skill overlap score (0-100).
    Returns (score, matched_req, matched_pref, missing_req, missing_pref).
    """
    if not required and not preferred:
        return 10.0, [], [], [], []

    matched_req = sorted(resume_skills & required)
    missing_req = sorted(required - resume_skills)
    matched_pref = sorted(resume_skills & preferred)
    missing_pref = sorted(preferred - resume_skills)

    req_score = (len(matched_req) / len(required) * 100) if required else 10.0
    pref_score = (len(matched_pref) / len(preferred) * 100) if preferred else 0.0

    overlap = req_score * REQUIRED_SKILL_W + pref_score * PREFERRED_SKILL_W
    return overlap, matched_req, matched_pref, missing_req, missing_pref


def _build_skill_contributions(
    matched_req: list[str],
    matched_pref: list[str],
    missing_req: list[str],
    required: set[str],
    preferred: set[str],
) -> list[SkillContribution]:
    """Build per-skill SHAP-style contribution objects."""
    contributions: list[SkillContribution] = []

    num_req = max(len(required), 1)
    num_pref = max(len(preferred), 1)

    for s in matched_req:
        contributions.append(
            SkillContribution(
                skill=s,
                impact=round(REQUIRED_SKILL_W / num_req * 100, 1),
                kind="required",
            )
        )
    for s in matched_pref:
        contributions.append(
            SkillContribution(
                skill=s,
                impact=round(PREFERRED_SKILL_W / num_pref * 100, 1),
                kind="preferred",
            )
        )
    for s in missing_req:
        contributions.append(
            SkillContribution(
                skill=s,
                impact=-round(REQUIRED_SKILL_W / num_req * 100, 1),
                kind="missing",
            )
        )

    contributions.sort(key=lambda c: abs(c.impact), reverse=True)
    return contributions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Pre-filter: cheap skill overlap pass
# ---------------------------------------------------------------------------
_PREFILTER_LIMIT = 200  # max jobs sent to SBERT


def _prefilter_by_skills(
    resume_skills: set[str],
    jobs: list[JobPosting],
    limit: int = _PREFILTER_LIMIT,
) -> list[tuple[JobPosting, float, list[str], list[str], list[str]]]:
    """Return (job, skill_score, m_req, m_pref, miss_req) sorted by skill score."""
    scored: list[tuple[JobPosting, float, list[str], list[str], list[str]]] = []
    for job in jobs:
        req_set = {s.lower() for s in job.required_skills}
        pref_set = {s.lower() for s in job.preferred_skills}
        sk_score, m_req, m_pref, miss_req, _ = _skill_overlap(
            resume_skills, req_set, pref_set
        )
        scored.append((job, sk_score, m_req, m_pref, miss_req))
    scored.sort(key=lambda x: -x[1])
    return scored[:limit]


# ---------------------------------------------------------------------------
# Single-job match (kept for API compatibility)
# ---------------------------------------------------------------------------

def match_resume_to_job(
    resume_text: str,
    resume_skills: list[str],
    job: JobPosting,
) -> MatchResult:
    """Compute a combined match score for one resume + one job."""
    resume_set = {s.lower() for s in resume_skills}
    req_set = {s.lower() for s in job.required_skills}
    pref_set = {s.lower() for s in job.preferred_skills}

    sk_score, m_req, m_pref, miss_req, _ = _skill_overlap(
        resume_set, req_set, pref_set
    )

    sem_score = 0.0
    sbert = _get_sbert()
    if sbert is not None and job.description:
        try:
            emb = sbert.encode([resume_text[:2000], job.description[:2000]])
            sem_score = max(0.0, _cosine_sim(emb[0], emb[1])) * 100
        except Exception:
            sem_score = 0.0

    exp_score = _experience_score(resume_text, job.experience_level) * 100

    overall = (
        SEMANTIC_WEIGHT * sem_score
        + SKILL_OVERLAP_WEIGHT * sk_score
        + EXPERIENCE_WEIGHT * exp_score
    )

    contributions = _build_skill_contributions(
        m_req, m_pref, miss_req, req_set, pref_set
    )

    return MatchResult(
        job=job,
        overall_score=round(overall, 1),
        semantic_score=round(sem_score, 1),
        skill_score=round(sk_score, 1),
        experience_score=round(exp_score, 1),
        matched_required=m_req,
        matched_preferred=m_pref,
        missing_required=miss_req,
        skill_contributions=contributions,
    )


# ---------------------------------------------------------------------------
# Batch matching (fast path)
# ---------------------------------------------------------------------------

def match_resume_to_jobs(
    resume_text: str,
    resume_skills: list[str],
    jobs: list[JobPosting],
    top_n: int = 20,
    min_score: float = 0.0,
) -> list[MatchResult]:
    """
    Rank *jobs* against a resume and return the top *top_n* results.

    Optimised pipeline:
        1. Pre-filter to top ~200 jobs by cheap skill-overlap.
        2. Batch-encode job descriptions with SBERT in one call.
        3. Vectorised cosine similarity.
    """
    if not jobs:
        return []

    resume_set = {s.lower() for s in resume_skills}

    # --- Stage 1: cheap pre-filter by skill overlap ----------------------
    candidates = _prefilter_by_skills(resume_set, jobs, limit=_PREFILTER_LIMIT)

    # --- Stage 2: batch SBERT encoding -----------------------------------
    sbert = _get_sbert()
    sem_scores: dict[str, float] = {}

    if sbert is not None:
        # Collect descriptions worth encoding
        desc_texts: list[str] = []
        desc_job_ids: list[str] = []
        for job, *_ in candidates:
            if job.description:
                desc_texts.append(job.description[:2000])
                desc_job_ids.append(job.job_id)

        if desc_texts:
            resume_emb = sbert.encode([resume_text[:2000]], show_progress_bar=False)
            job_embs = sbert.encode(desc_texts, batch_size=64, show_progress_bar=False)
            sims = _batch_cosine_sim(resume_emb[0], job_embs)
            for jid, sim in zip(desc_job_ids, sims):
                sem_scores[jid] = max(0.0, float(sim)) * 100

    # --- Stage 3: assemble MatchResults ----------------------------------
    results: list[MatchResult] = []
    for job, sk_score, m_req, m_pref, miss_req in candidates:
        sem_score = sem_scores.get(job.job_id, 0.0)
        exp_score = _experience_score(resume_text, job.experience_level) * 100

        overall = (
            SEMANTIC_WEIGHT * sem_score
            + SKILL_OVERLAP_WEIGHT * sk_score
            + EXPERIENCE_WEIGHT * exp_score
        )
        if overall < min_score:
            continue

        req_set = {s.lower() for s in job.required_skills}
        pref_set = {s.lower() for s in job.preferred_skills}
        contributions = _build_skill_contributions(
            m_req, m_pref, miss_req, req_set, pref_set
        )

        results.append(
            MatchResult(
                job=job,
                overall_score=round(overall, 1),
                semantic_score=round(sem_score, 1),
                skill_score=round(sk_score, 1),
                experience_score=round(exp_score, 1),
                matched_required=m_req,
                matched_preferred=m_pref,
                missing_required=miss_req,
                skill_contributions=contributions,
            )
        )

    results.sort(
        key=lambda r: (
            -r.overall_score,
            -(len(r.matched_required) + len(r.matched_preferred)),
        )
    )
    return results[:top_n]


def jobs_df_to_postings(df: pd.DataFrame) -> list[JobPosting]:
    """Convert the legacy ``jobs_parsed.csv`` DataFrame into ``JobPosting`` objects.

    Uses vectorised column access instead of iterrows for speed.
    """
    def _split(val: object) -> list[str]:
        s = str(val)
        if s in ("", "nan", "None"):
            return []
        return [t.strip() for t in s.split(",") if t.strip()]

    cols = {
        "job_id": df.get("job_id", pd.Series(dtype=str)).astype(str).tolist(),
        "title": df.get("title", pd.Series(["Unknown"] * len(df))).fillna("Unknown").astype(str).tolist(),
        "company": df.get("company_name", pd.Series(["Unknown"] * len(df))).fillna("Unknown").astype(str).tolist(),
        "description": df.get("description", pd.Series([""] * len(df))).fillna("").astype(str).tolist(),
        "required_skills": df.get("required_skills", pd.Series([""] * len(df))).fillna("").tolist(),
        "preferred_skills": df.get("preferred_skills", pd.Series([""] * len(df))).fillna("").tolist(),
        "location": df.get("location", pd.Series(["Unknown"] * len(df))).fillna("Unknown").astype(str).tolist(),
        "salary": df.get("normalized_salary", pd.Series([None] * len(df))).tolist(),
        "remote": df.get("remote_allowed", pd.Series([0] * len(df))).fillna(0).tolist(),
        "experience": df.get("formatted_experience_level", pd.Series(["Not specified"] * len(df))).fillna("Not specified").astype(str).tolist(),
    }

    postings: list[JobPosting] = []
    for i in range(len(df)):
        sal = cols["salary"][i]
        sal_val = sal if pd.notna(sal) else None
        postings.append(
            JobPosting(
                job_id=cols["job_id"][i],
                title=cols["title"][i],
                company=cols["company"][i],
                description=cols["description"][i],
                required_skills=_split(cols["required_skills"][i]),
                preferred_skills=_split(cols["preferred_skills"][i]),
                location=cols["location"][i],
                salary_min=sal_val,
                salary_max=sal_val,
                remote=bool(cols["remote"][i]),
                experience_level=cols["experience"][i],
                source="linkedin_static",
            )
        )
    return postings
