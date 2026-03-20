"""
Canonical fairness evaluation component for FAIR-PATH.

This evaluator focuses on two practical fairness layers:
1. lexical bias detection in resume content
2. mitigation via anonymization and fairness-sensitive score comparison
"""
from __future__ import annotations

import re

from src.config.settings import FAIRNESS_BIAS_CATEGORIES
from src.models.schemas import BiasIndicator, FairnessReport


_SYNTHETIC_VARIANTS = {
    "male_name": "Rahul Sharma",
    "female_name": "Priya Sharma",
    "western_name": "John Smith",
    "south_asian_name": "Amit Patel",
}


def _scan_bias_indicators(resume_text: str) -> tuple[list[BiasIndicator], dict[str, list[str]], float]:
    text_lower = resume_text.lower()
    indicators: list[BiasIndicator] = []
    category_hits: dict[str, list[str]] = {}
    total_penalty = 0.0

    for category, cfg in FAIRNESS_BIAS_CATEGORIES.items():
        hits: list[str] = []
        for token in cfg["indicators"]:
            matches = re.findall(r"\b" + re.escape(token.lower()) + r"\b", text_lower)
            if not matches:
                continue
            occurrences = len(matches)
            penalty = float(cfg["penalty"]) * occurrences
            total_penalty += penalty
            hits.append(token)
            indicators.append(
                BiasIndicator(
                    word=token,
                    category=category,
                    occurrences=occurrences,
                    penalty=round(penalty, 2),
                    description=f"'{token}' found {occurrences} time(s) and may introduce demographic bias.",
                )
            )
        category_hits[category] = hits

    indicators.sort(key=lambda item: (-item.penalty, item.word))
    return indicators, category_hits, total_penalty


def _bias_level(hit_words: list[str]) -> str:
    if not hit_words:
        return "None detected"
    if len(hit_words) >= 3:
        return "High"
    if len(hit_words) >= 2:
        return "Moderate"
    return "Low"


def anonymize_resume_text(resume_text: str) -> str:
    text = resume_text
    text = re.sub(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", "[email removed]", text, flags=re.IGNORECASE)
    text = re.sub(r"\+?\d[\d\s().-]{7,}\d", "[phone removed]", text)
    text = re.sub(r"\b(mr|mrs|ms|miss|mx)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?", "[name removed]", text)
    text = re.sub(r"\b(date of birth|dob|born in)\b[:\s-]*[^\n]+", "[dob removed]", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(marital status|married|single|divorced)\b[:\s-]*[^\n]+", "[family details removed]", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(he/him|she/her|male|female|man|woman)\b", "[demographic removed]", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(nationality|race|ethnicity|religion|caste)\b[:\s-]*[^\n]+", "[identity removed]", text, flags=re.IGNORECASE)
    return text


def _estimate_variant_scores(
    score: float,
    indicators: list[BiasIndicator],
    category_hits: dict[str, list[str]],
) -> tuple[dict[str, float], float]:
    total_indicator_penalty = sum(indicator.penalty for indicator in indicators)
    variant_penalty = min(total_indicator_penalty * 0.03, 8.0)

    variant_scores = {variant_name: round(score, 2) for variant_name in _SYNTHETIC_VARIANTS}
    if category_hits.get("Gender Bias"):
        variant_scores["female_name"] = round(max(0.0, score - variant_penalty), 2)
    if category_hits.get("Ethnicity / Nationality Bias"):
        variant_scores["south_asian_name"] = round(max(0.0, score - variant_penalty), 2)
    if category_hits.get("Marital / Family Bias"):
        variant_scores["female_name"] = round(max(0.0, variant_scores["female_name"] - variant_penalty / 2), 2)
    if category_hits.get("Age Bias"):
        variant_scores["western_name"] = round(max(0.0, score - variant_penalty / 2), 2)

    if not variant_scores:
        return {}, 0.0

    scores = list(variant_scores.values())
    dpd = max(scores) - min(scores) if scores else 0.0
    return variant_scores, round(dpd / 100.0, 4)


def evaluate_fairness(resume_text: str) -> FairnessReport:
    indicators, category_hits, total_penalty = _scan_bias_indicators(resume_text)
    base_score = round(max(0.0, 100.0 - total_penalty), 1)

    year_mentions = len(re.findall(r"\b\d{1,2}\+?\s*years?\b", resume_text.lower()))
    experience_bias = "None detected"
    if year_mentions >= 5:
        experience_bias = "Moderate"
    elif year_mentions >= 3:
        experience_bias = "Low"

    anonymized_text = anonymize_resume_text(resume_text)
    mitigated_indicators, _, mitigated_penalty = _scan_bias_indicators(anonymized_text)
    mitigated_score = round(max(0.0, 100.0 - mitigated_penalty), 1)

    variant_scores, dpd = _estimate_variant_scores(base_score, indicators, category_hits)

    recommendations: list[str] = []
    if category_hits.get("Gender Bias"):
        recommendations.append("Remove gendered salutations, pronouns, and explicit gender references.")
    if category_hits.get("Age Bias"):
        recommendations.append("Remove age, date of birth, and non-essential graduation year details.")
    if category_hits.get("Ethnicity / Nationality Bias"):
        recommendations.append("Remove nationality, race, religion, or caste references unless legally required.")
    if category_hits.get("Marital / Family Bias"):
        recommendations.append("Remove marital status and family details from the resume.")
    if category_hits.get("Photo / Appearance Bias"):
        recommendations.append("Avoid photos or appearance-related references in resume text.")
    if category_hits.get("Education Prestige Bias"):
        recommendations.append("Focus on skills, outcomes, and projects instead of prestige labels.")
    if not recommendations:
        recommendations.append("No major demographic-bias signals detected in the resume text.")

    preview = anonymized_text[:300] + ("..." if len(anonymized_text) > 300 else "")
    return FairnessReport(
        score=base_score,
        gender_bias=_bias_level(category_hits.get("Gender Bias", [])),
        age_bias=_bias_level(category_hits.get("Age Bias", [])),
        education_bias=_bias_level(category_hits.get("Education Prestige Bias", [])),
        experience_bias=experience_bias,
        indicators=indicators,
        recommendations=recommendations,
        mitigation_applied=mitigated_score > base_score,
        mitigated_score=mitigated_score,
        demographic_parity_difference=dpd,
        variant_scores=variant_scores,
        anonymized_text_preview=preview,
    )
