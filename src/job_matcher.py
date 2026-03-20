"""
Canonical job matcher component for FAIR-PATH.

This module is the public entrypoint for Component 4. It provides:
    - deterministic skill/experience-based matching
    - optional semantic matching through Sentence-BERT
    - conversion from parsed job DataFrames to JobPosting objects
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.config.settings import (
    EXPERIENCE_WEIGHT,
    PREFERRED_SKILL_W,
    REQUIRED_SKILL_W,
    SEMANTIC_WEIGHT,
    SKILL_OVERLAP_WEIGHT,
)
from src.matching.semantic_matcher import (
    _get_sbert,
    _batch_cosine_sim,
    _build_skill_contributions,
    _experience_score,
)
from src.models.schemas import JobPosting, MatchResult


@dataclass(slots=True)
class JobMatcherConfig:
    use_semantic: bool = True
    top_n: int = 20
    min_score: float = 0.0
    prefilter_limit: int = 200


def _skill_overlap(
    resume_skills: set[str],
    required: set[str],
    preferred: set[str],
) -> tuple[float, list[str], list[str], list[str], list[str]]:
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


def _prefilter_jobs(
    resume_skills: set[str],
    jobs: list[JobPosting],
    limit: int,
) -> list[tuple[JobPosting, float, list[str], list[str], list[str]]]:
    scored: list[tuple[JobPosting, float, list[str], list[str], list[str]]] = []
    for job in jobs:
        req_set = {skill.lower() for skill in job.required_skills}
        pref_set = {skill.lower() for skill in job.preferred_skills}
        skill_score, matched_req, matched_pref, missing_req, _ = _skill_overlap(
            resume_skills,
            req_set,
            pref_set,
        )
        scored.append((job, skill_score, matched_req, matched_pref, missing_req))

    scored.sort(key=lambda item: (-item[1], -len(item[2]), -len(item[3])))
    return scored[:limit]


class JobMatcher:
    def __init__(self, config: JobMatcherConfig | None = None):
        self.config = config or JobMatcherConfig()

    def match_resume_to_job(
        self,
        resume_text: str,
        resume_skills: list[str],
        job: JobPosting,
    ) -> MatchResult:
        return self.match_resume_to_jobs(resume_text, resume_skills, [job], top_n=1)[0]

    def match_resume_to_jobs(
        self,
        resume_text: str,
        resume_skills: list[str],
        jobs: list[JobPosting],
        *,
        top_n: int | None = None,
        min_score: float | None = None,
    ) -> list[MatchResult]:
        if not jobs:
            return []

        top_n = self.config.top_n if top_n is None else top_n
        min_score = self.config.min_score if min_score is None else min_score
        resume_set = {skill.lower().strip() for skill in resume_skills}
        candidates = _prefilter_jobs(resume_set, jobs, self.config.prefilter_limit)

        semantic_scores: dict[str, float] = {}
        if self.config.use_semantic:
            sbert = _get_sbert()
            if sbert is not None:
                descriptions = [job.description[:2000] for job, *_ in candidates if job.description]
                description_job_ids = [job.job_id for job, *_ in candidates if job.description]
                if descriptions:
                    resume_embedding = sbert.encode([resume_text[:2000]], show_progress_bar=False)
                    job_embeddings = sbert.encode(
                        descriptions,
                        batch_size=64,
                        show_progress_bar=False,
                    )
                    similarities = _batch_cosine_sim(resume_embedding[0], job_embeddings)
                    semantic_scores = {
                        job_id: max(0.0, float(score)) * 100
                        for job_id, score in zip(description_job_ids, similarities)
                    }

        results: list[MatchResult] = []
        for job, skill_score, matched_req, matched_pref, missing_req in candidates:
            req_set = {skill.lower() for skill in job.required_skills}
            pref_set = {skill.lower() for skill in job.preferred_skills}
            semantic_score = semantic_scores.get(job.job_id, 0.0)
            experience_score = _experience_score(resume_text, job.experience_level) * 100

            overall_score = (
                SEMANTIC_WEIGHT * semantic_score
                + SKILL_OVERLAP_WEIGHT * skill_score
                + EXPERIENCE_WEIGHT * experience_score
            )
            if overall_score < min_score:
                continue

            results.append(
                MatchResult(
                    job=job,
                    overall_score=round(overall_score, 1),
                    semantic_score=round(semantic_score, 1),
                    skill_score=round(skill_score, 1),
                    experience_score=round(experience_score, 1),
                    matched_required=matched_req,
                    matched_preferred=matched_pref,
                    missing_required=missing_req,
                    skill_contributions=_build_skill_contributions(
                        matched_req,
                        matched_pref,
                        missing_req,
                        req_set,
                        pref_set,
                    ),
                )
            )

        results.sort(
            key=lambda result: (
                -result.overall_score,
                -(len(result.matched_required) + len(result.matched_preferred)),
            )
        )
        return results[:top_n]


def match_resume_to_job(
    resume_text: str,
    resume_skills: list[str],
    job: JobPosting,
    *,
    use_semantic: bool = True,
) -> MatchResult:
    return JobMatcher(JobMatcherConfig(use_semantic=use_semantic)).match_resume_to_job(
        resume_text,
        resume_skills,
        job,
    )


def match_resume_to_jobs(
    resume_text: str,
    resume_skills: list[str],
    jobs: list[JobPosting],
    *,
    top_n: int = 20,
    min_score: float = 0.0,
    use_semantic: bool = True,
) -> list[MatchResult]:
    return JobMatcher(
        JobMatcherConfig(
            use_semantic=use_semantic,
            top_n=top_n,
            min_score=min_score,
        )
    ).match_resume_to_jobs(
        resume_text,
        resume_skills,
        jobs,
        top_n=top_n,
        min_score=min_score,
    )


def jobs_df_to_postings(df: pd.DataFrame) -> list[JobPosting]:
    def _split(value: object) -> list[str]:
        text = str(value)
        if text in ("", "nan", "None"):
            return []
        return [token.strip() for token in text.split(",") if token.strip()]

    columns = {
        "job_id": df.get("job_id", pd.Series(dtype=str)).astype(str).tolist(),
        "title": df.get("title", pd.Series(["Unknown"] * len(df))).fillna("Unknown").astype(str).tolist(),
        "company": df.get("company_name", pd.Series(["Unknown"] * len(df))).fillna("Unknown").astype(str).tolist(),
        "description": df.get("description", pd.Series([""] * len(df))).fillna("").astype(str).tolist(),
        "required_skills": df.get("required_skills", pd.Series([""] * len(df))).fillna("").tolist(),
        "preferred_skills": df.get("preferred_skills", pd.Series([""] * len(df))).fillna("").tolist(),
        "location": df.get("location", pd.Series(["Unknown"] * len(df))).fillna("Unknown").astype(str).tolist(),
        "salary": df.get("normalized_salary", pd.Series([None] * len(df))).tolist(),
        "remote": df.get("remote_allowed", pd.Series([0] * len(df))).fillna(0).tolist(),
        "experience": df.get(
            "formatted_experience_level",
            pd.Series(["Not specified"] * len(df)),
        ).fillna("Not specified").astype(str).tolist(),
    }

    postings: list[JobPosting] = []
    for index in range(len(df)):
        salary_value = columns["salary"][index]
        if pd.isna(salary_value):
            salary_value = None

        postings.append(
            JobPosting(
                job_id=columns["job_id"][index],
                title=columns["title"][index],
                company=columns["company"][index],
                description=columns["description"][index],
                required_skills=_split(columns["required_skills"][index]),
                preferred_skills=_split(columns["preferred_skills"][index]),
                location=columns["location"][index],
                salary_min=salary_value,
                salary_max=salary_value,
                remote=bool(columns["remote"][index]),
                experience_level=columns["experience"][index],
                source="linkedin_static",
            )
        )
    return postings
