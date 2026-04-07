"""
Skill proficiency estimator for FAIR-PATH.

Moves beyond binary "has skill" matching by reading the context around a
skill mention and estimating a practical proficiency level:
    basic -> intermediate -> advanced -> expert
"""
from __future__ import annotations

import re
from dataclasses import dataclass


LEVEL_TO_SCORE = {
    "basic": 0.45,
    "intermediate": 0.70,
    "advanced": 0.88,
    "expert": 1.00,
}


_LEVEL_ORDER = ("basic", "intermediate", "advanced", "expert")

_KEYWORDS = {
    "basic": [
        "basic",
        "beginner",
        "novice",
        "introductory",
        "familiar with",
        "learned",
        "learning",
        "coursework",
        "academic",
        "student",
    ],
    "intermediate": [
        "hands-on",
        "built",
        "developed",
        "implemented",
        "created",
        "worked with",
        "experience with",
        "used in projects",
        "personal project",
        "internship",
    ],
    "advanced": [
        "advanced",
        "proficient",
        "production",
        "optimized",
        "designed",
        "architected",
        "led",
        "deployed",
        "scalable",
        "open-source",
    ],
    "expert": [
        "expert",
        "subject matter expert",
        "published",
        "pioneered",
        "invented",
        "created framework",
        "authored",
        "mentored",
        "research",
        "at scale",
    ],
}

_ACTION_VERBS = {
    "basic": {"learned", "studied", "explored", "used"},
    "intermediate": {"built", "developed", "implemented", "integrated", "created"},
    "advanced": {"architected", "led", "optimized", "designed", "deployed"},
    "expert": {"invented", "published", "pioneered", "authored", "founded"},
}

_YEARS_PATTERNS = [
    re.compile(r"(\d+(?:\.\d+)?)\+?\s+years?[^.\n]{0,40}?\b(?:of\s+)?experience\b", re.IGNORECASE),
    re.compile(r"(\d+(?:\.\d+)?)\+?\s+years?[^.\n]{0,20}?\bwith\b", re.IGNORECASE),
    re.compile(r"(\d+(?:\.\d+)?)\+?\s+years?[^.\n]{0,20}?\bin\b", re.IGNORECASE),
]

_QUANT_PATTERN = re.compile(
    r"\b\d+(?:\+|%|k|K)?\b|\b(?:improved|reduced|increased|scaled|built|processed|ingested)\b",
    re.IGNORECASE,
)


@dataclass(slots=True)
class ProficiencyEstimate:
    level: str
    score: float
    evidence: list[str]


def _windows(text: str, skill: str, radius: int = 180) -> list[str]:
    pattern = re.compile(r"\b" + re.escape(skill) + r"\b", re.IGNORECASE)
    windows: list[str] = []
    for match in pattern.finditer(text):
        start = max(0, match.start() - radius)
        end = min(len(text), match.end() + radius)
        windows.append(text[start:end].lower())
    return windows[:5]


def _years_signal(window: str) -> tuple[str | None, str | None]:
    for pattern in _YEARS_PATTERNS:
        match = pattern.search(window)
        if not match:
            continue
        years = float(match.group(1))
        if years >= 6:
            return "expert", f"{years:g}+ years of experience"
        if years >= 4:
            return "advanced", f"{years:g}+ years of experience"
        if years >= 2:
            return "intermediate", f"{years:g}+ years of experience"
        return "basic", f"{years:g}+ years of experience"
    return None, None


def _keyword_signal(window: str) -> tuple[str | None, str | None]:
    for level in ("expert", "advanced", "intermediate", "basic"):
        for keyword in _KEYWORDS[level]:
            if keyword in window:
                return level, keyword
    return None, None


def _verb_signal(window: str) -> tuple[str | None, str | None]:
    tokens = set(re.findall(r"[a-zA-Z][a-zA-Z\-]+", window))
    for level in ("expert", "advanced", "intermediate", "basic"):
        overlap = _ACTION_VERBS[level] & tokens
        if overlap:
            return level, sorted(overlap)[0]
    return None, None


def _project_complexity_bonus(window: str) -> tuple[int, str | None]:
    hits = _QUANT_PATTERN.findall(window)
    if len(hits) >= 4:
        return 2, "quantified project impact"
    if len(hits) >= 2:
        return 1, "project evidence"
    return 0, None


def estimate_skill_proficiency(text: str, skill: str) -> ProficiencyEstimate:
    windows = _windows(text, skill)
    if not windows:
        return ProficiencyEstimate("intermediate", LEVEL_TO_SCORE["intermediate"], [])

    level_points = {level: 0 for level in _LEVEL_ORDER}
    evidence: list[str] = []

    for window in windows:
        years_level, years_evidence = _years_signal(window)
        if years_level:
            level_points[years_level] += 4
            evidence.append(years_evidence)

        keyword_level, keyword_evidence = _keyword_signal(window)
        if keyword_level:
            level_points[keyword_level] += 2
            evidence.append(keyword_evidence)

        verb_level, verb_evidence = _verb_signal(window)
        if verb_level:
            level_points[verb_level] += 1
            evidence.append(verb_evidence)

        bonus, bonus_evidence = _project_complexity_bonus(window)
        if bonus:
            if level_points["expert"] > 0:
                level_points["expert"] += bonus
            elif level_points["advanced"] > 0:
                level_points["advanced"] += bonus
            else:
                level_points["intermediate"] += bonus
            evidence.append(bonus_evidence)

    # favor higher levels on ties if there is explicit evidence
    best_level = "intermediate"
    best_points = -1
    for level in _LEVEL_ORDER:
        points = level_points[level]
        if points >= best_points:
            best_level = level
            best_points = points

    if best_points <= 0:
        best_level = "intermediate"

    deduped_evidence: list[str] = []
    seen: set[str] = set()
    for item in evidence:
        if not item or item in seen:
            continue
        seen.add(item)
        deduped_evidence.append(item)

    return ProficiencyEstimate(
        level=best_level,
        score=LEVEL_TO_SCORE[best_level],
        evidence=deduped_evidence[:4],
    )


def detect_proficiency(text: str, skill: str) -> str:
    return estimate_skill_proficiency(text, skill).level
