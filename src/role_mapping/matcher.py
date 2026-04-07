"""
Role Matcher
=============
Given a set of extracted skills, computes which job roles are the best fit.
Returns roles ranked by a composite score of core-skill coverage and bonus-skill overlap.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re

from src.job_roles_database import load_job_roles
from src.models.schemas import ExtractedSkill
from src.skill_extraction.normalizer import normalize_skill
from src.skill_extraction.proficiency import LEVEL_TO_SCORE


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
    proficiency_alignment: float = 0.0


def match_roles(
    resume_skills: list[str],
    extracted_skills: list[ExtractedSkill] | None = None,
    resume_text: str | None = None,
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
    resume_set = {normalize_skill(s) for s in resume_skills if str(s).strip()}
    proficiency_by_skill = {
        normalize_skill(skill.canonical): float(getattr(skill, "proficiency_score", LEVEL_TO_SCORE.get(skill.proficiency, 0.7)))
        for skill in (extracted_skills or [])
    }
    resume_text_lower = (resume_text or "").lower()

    inferred_skills: set[str] = set()
    pattern_skill_map = {
        "llm": [r"\bllm\b", r"\bllms\b", r"large language model"],
        "retrieval-augmented generation": [r"\brag\b", r"retrieval[- ]augmented generation"],
        "langchain": [r"\blangchain\b"],
        "groq": [r"\bgroq\b"],
        "transformers": [r"\btransformers\b", r"\bbert\b", r"\bllama\b", r"\bgpt\b"],
        "vector database": [r"vector database", r"vector databases", r"\bchromadb\b", r"\bpinecone\b", r"\bweaviate\b", r"\bfaiss\b", r"\bqdrant\b"],
        "generative ai": [r"generative ai", r"\bmultimodal ai\b"],
    }
    for inferred_skill, patterns in pattern_skill_map.items():
        if any(re.search(pattern, resume_text_lower) for pattern in patterns):
            inferred_skills.add(inferred_skill)
    resume_set |= inferred_skills

    results: list[RoleMatch] = []
    for entry in load_job_roles():
        core = list(entry.core_skills)
        optional = list(entry.optional_skills)

        matched_core = [s for s in core if s in resume_set]
        matched_opt = [s for s in optional if s in resume_set]
        missing_core = [s for s in core if s not in resume_set]

        if not matched_core and not matched_opt:
            continue

        core_coverage = sum(proficiency_by_skill.get(s, 0.7) for s in matched_core)
        opt_coverage = sum(proficiency_by_skill.get(s, 0.7) for s in matched_opt)
        core_pct = (core_coverage / len(core)) if core else 0.0
        opt_pct = (opt_coverage / len(optional)) if optional else 0.0

        score = core_pct * 75.0 + opt_pct * 25.0

        if entry.domain.lower() == "ai/ml":
            ai_signal_terms = {
                "llm", "retrieval-augmented generation", "langchain", "groq",
                "vector database", "generative ai", "transformers",
            }
            ai_signal_count = len(ai_signal_terms & resume_set)
            score += min(ai_signal_count * 3.0, 12.0)

        if resume_text_lower and entry.role.lower() in resume_text_lower:
            score += 4.0

        if score < min_score:
            continue

        results.append(
            RoleMatch(
                role=entry.role,
                domain=entry.domain,
                description=entry.description,
                score=round(min(score, 100.0), 1),
                core_match_pct=round(core_pct * 100, 1),
                matched_core=matched_core,
                matched_optional=matched_opt,
                missing_core=missing_core,
                total_matched=len(matched_core) + len(matched_opt),
                proficiency_alignment=round(core_pct * 100, 1),
            )
        )

    results.sort(key=lambda r: (-r.score, -r.total_matched))
    return results[:top_n]
