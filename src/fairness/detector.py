"""
Fairness Detection Module
=========================
Detects possible biases in the resume evaluation pipeline:

    - Gender bias
    - Age bias
    - Ethnicity / nationality bias
    - Marital / family bias
    - Photo / appearance bias
    - Education prestige bias

Produces a ``FairnessReport`` with per-word SHAP-style contributions
and an overall fairness score (0-100).
"""
from __future__ import annotations

import re
from collections import Counter

from src.config.settings import FAIRNESS_BIAS_CATEGORIES
from src.models.schemas import BiasIndicator, FairnessReport


def evaluate_fairness(resume_text: str) -> FairnessReport:
    """
    Analyse *resume_text* for bias-introducing signals.

    Returns a :class:`FairnessReport` with:
        - ``score`` 0-100  (100 = no bias detected)
        - per-category bias labels
        - per-word ``indicators`` with point penalties
        - actionable ``recommendations``
    """
    text_lower = resume_text.lower()
    total_penalty = 0.0
    indicators: list[BiasIndicator] = []
    category_hits: dict[str, list[str]] = {}

    for category, cfg in FAIRNESS_BIAS_CATEGORIES.items():
        hit_words: list[str] = []
        for word in cfg["indicators"]:
            # Count occurrences with word boundary
            matches = re.findall(r"\b" + re.escape(word) + r"\b", text_lower)
            count = len(matches)
            if count == 0:
                continue
            penalty = cfg["penalty"] * count
            total_penalty += penalty
            hit_words.append(word)
            indicators.append(
                BiasIndicator(
                    word=word,
                    category=category,
                    occurrences=count,
                    penalty=penalty,
                    description=f"'{word}' found {count} time(s) → −{penalty} pts",
                )
            )
        category_hits[category] = hit_words

    # Sort indicators by penalty descending
    indicators.sort(key=lambda i: -i.penalty)

    score = max(0.0, 100.0 - total_penalty)

    # Build per-category summary strings
    def _level(words: list[str]) -> str:
        if not words:
            return "None detected"
        if len(words) >= 3:
            return "High"
        if len(words) >= 2:
            return "Moderate"
        return "Low"

    gender = _level(category_hits.get("Gender Bias", []))
    age = _level(category_hits.get("Age Bias", []))
    education = _level(category_hits.get("Education Prestige Bias", []))

    # Experience bias: heuristic – is the resume relying heavily on years?
    year_mentions = len(re.findall(r"\b\d{1,2}\+?\s*years?\b", text_lower))
    experience = "None detected"
    if year_mentions >= 5:
        experience = "Moderate"
    elif year_mentions >= 3:
        experience = "Low"

    # Recommendations
    recs: list[str] = []
    if gender != "None detected":
        recs.append("Remove gendered salutations (Mr./Mrs./Ms.) and pronouns.")
    if age != "None detected":
        recs.append("Remove age, date of birth, and graduation year if > 15 years ago.")
    if education != "None detected":
        recs.append("Focus on skills & achievements rather than university prestige labels.")
    if any(category_hits.get("Marital / Family Bias", [])):
        recs.append("Remove marital status, children, or family details.")
    if any(category_hits.get("Photo / Appearance Bias", [])):
        recs.append("Remove photo/headshot references for unbiased evaluation.")
    if any(category_hits.get("Ethnicity / Nationality Bias", [])):
        recs.append("Remove nationality, race, or religion references.")
    if not recs:
        recs.append("Your resume looks bias-free — great job!")

    return FairnessReport(
        score=round(score, 1),
        gender_bias=gender,
        age_bias=age,
        education_bias=education,
        experience_bias=experience,
        indicators=indicators,
        recommendations=recs,
    )
