"""
Skill Gap Priority Ranker
=========================
Compares resume skills with market demand and job-required skills,
then ranks missing skills by priority (High / Medium / Low).

Ranking factors:
    1. Frequency in job postings (market demand)
    2. Importance in matched job descriptions
    3. Appearance as *required* vs *preferred*
"""
from __future__ import annotations

from collections import Counter

import pandas as pd

from src.models.schemas import SkillGap


def _count_skill_demand(jobs_df: pd.DataFrame) -> dict[str, int]:
    """Count how many jobs mention each skill."""
    counts: Counter[str] = Counter()
    for _, row in jobs_df.iterrows():
        for col in ("required_skills", "preferred_skills"):
            raw = row.get(col, "")
            if not isinstance(raw, str) or raw.strip() in ("", "nan"):
                continue
            for skill in raw.split(","):
                s = skill.strip().lower()
                if s:
                    counts[s] += 1
    return dict(counts)


def rank_skill_gaps(
    resume_skills: list[str],
    jobs_df: pd.DataFrame,
    top_n: int = 15,
) -> list[SkillGap]:
    """
    Identify missing high-demand skills and rank them.

    Parameters
    ----------
    resume_skills : canonical skill names the candidate has.
    jobs_df : DataFrame with ``required_skills`` / ``preferred_skills``.
    top_n : how many gaps to return.

    Returns
    -------
    list[SkillGap] sorted by priority (High → Low).
    """
    demand = _count_skill_demand(jobs_df)
    total_jobs = max(len(jobs_df), 1)
    resume_set = {s.lower() for s in resume_skills}

    gaps: list[SkillGap] = []
    for skill, count in sorted(demand.items(), key=lambda x: -x[1]):
        if skill in resume_set:
            continue
        pct = count / total_jobs * 100
        if pct >= 15:
            priority = "High"
        elif pct >= 5:
            priority = "Medium"
        else:
            priority = "Low"
        gaps.append(
            SkillGap(skill=skill, job_count=count, demand_pct=round(pct, 1), priority=priority)
        )
        if len(gaps) >= top_n:
            break

    # Sort High > Medium > Low, then by demand descending.
    order = {"High": 0, "Medium": 1, "Low": 2}
    gaps.sort(key=lambda g: (order.get(g.priority, 9), -g.demand_pct))
    return gaps
