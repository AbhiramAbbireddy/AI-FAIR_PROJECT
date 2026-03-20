"""
Evaluation 3: Explainability quality proxy for SHAP output.

This is an automated proxy evaluation, not a human user study.
"""
from __future__ import annotations

import json

from src.config.settings import BASE_DIR
from src.role_mapping.matcher import match_roles
from src.shap_explainer import MatchSHAPExplainer


SKILLS_PATH = BASE_DIR / "data" / "ground_truth_skills.json"
RESULTS_PATH = BASE_DIR / "results" / "shap_user_study.json"


def evaluate_shap() -> dict:
    with open(SKILLS_PATH, "r", encoding="utf-8") as file:
        skills_gt = json.load(file)

    explainer = MatchSHAPExplainer()
    understanding_votes = 0
    clarity_scores: list[float] = []
    details = []

    for resume_id, skills in skills_gt.items():
        role_matches = match_roles(skills, min_score=0, top_n=3)
        explanations = explainer.explain_role_matches(
            resume_text="Projects in " + ", ".join(skills),
            resume_skills=skills,
            role_matches=role_matches,
        )

        for role_match in role_matches:
            explanation = explanations.get(role_match.role, {})
            positive = explanation.get("positive_factors", [])
            negative = explanation.get("negative_factors", [])
            summary = explanation.get("summary", "")
            understood = bool(summary and positive and negative)
            understanding_votes += 1 if understood else 0
            clarity = min(5.0, 2.0 + len(positive) * 0.4 + len(negative) * 0.3 + (0.6 if summary else 0.0))
            clarity_scores.append(clarity)
            details.append(
                {
                    "resume_id": resume_id,
                    "role": role_match.role,
                    "understood_proxy": understood,
                    "clarity_proxy": round(clarity, 2),
                    "method": explanation.get("method", "unknown"),
                }
            )

    total = len(details)
    understanding_rate = understanding_votes / total if total else 0.0
    average_clarity = sum(clarity_scores) / len(clarity_scores) if clarity_scores else 0.0

    result = {
        "samples": total,
        "understanding_rate": round(understanding_rate, 4),
        "average_clarity": round(average_clarity, 4),
        "status": "meets_proxy_target" if understanding_rate >= 0.8 and average_clarity >= 4.0 else "needs_review",
        "evaluation_type": "automated_explanation_proxy",
        "details": details,
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)
    return result


if __name__ == "__main__":
    print(json.dumps(evaluate_shap(), indent=2))
