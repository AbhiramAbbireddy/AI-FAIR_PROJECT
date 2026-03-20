"""
Role Matcher
=============
Given a set of extracted skills, computes which job roles are the best fit.
Returns roles ranked by a composite score of core-skill coverage and bonus-skill overlap.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.job_roles_database import load_job_roles


@dataclass
class RoleMatch:
    role: str
    domain: str
    description: str
    score: float  # 0-100
    core_match_pct: float  # % of core skills matched
    matched_core: list[str] = field(default_factory=list)
    matched_optional: list[str] = field(default_factory=list)
    missing_core: list[str] = field(default_factory=list)
    total_matched: int = 0


def match_roles(
    resume_skills: list[str],
    min_score: float = 10.0,
    top_n: int = 10,
) -> list[RoleMatch]:
    """
    Rank job roles by how well *resume_skills* match each role's skill profile.

    Scoring:
        core_score   = (matched_core / total_core) * 70
        bonus_score  = (matched_optional / total_optional) * 30   (if any optional)
        total        = core_score + bonus_score
    """
    resume_set = {s.lower().strip() for s in resume_skills}

    results: list[RoleMatch] = []
    for entry in load_job_roles():
        core = list(entry.core_skills)
        optional = list(entry.optional_skills)

        matched_core = [s for s in core if s in resume_set]
        matched_opt = [s for s in optional if s in resume_set]
        missing_core = [s for s in core if s not in resume_set]

        if not matched_core and not matched_opt:
            continue

        core_pct = len(matched_core) / len(core) if core else 0.0
        opt_pct = len(matched_opt) / len(optional) if optional else 0.0

        score = core_pct * 70.0 + opt_pct * 30.0

        if score < min_score:
            continue

        results.append(
            RoleMatch(
                role=entry.role,
                domain=entry.domain,
                description=entry.description,
                score=round(score, 1),
                core_match_pct=round(core_pct * 100, 1),
                matched_core=matched_core,
                matched_optional=matched_opt,
                missing_core=missing_core,
                total_matched=len(matched_core) + len(matched_opt),
            )
        )

    results.sort(key=lambda r: (-r.score, -r.total_matched))
    return results[:top_n]
