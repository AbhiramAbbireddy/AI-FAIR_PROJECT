"""
Evaluation 2: Job/role matching accuracy using ground-truth role labels.
"""
from __future__ import annotations

import json

from src.config.settings import BASE_DIR
from src.role_mapping.matcher import match_roles


SKILLS_PATH = BASE_DIR / "data" / "ground_truth_skills.json"
MATCHES_PATH = BASE_DIR / "data" / "ground_truth_matches.json"
RESULTS_PATH = BASE_DIR / "results" / "matching_accuracy.json"


def evaluate_matching() -> dict:
    with open(SKILLS_PATH, "r", encoding="utf-8") as file:
        skills_gt = json.load(file)
    with open(MATCHES_PATH, "r", encoding="utf-8") as file:
        matches_gt = json.load(file)

    precisions = []
    details = []

    for resume_id, relevant_roles in matches_gt.items():
        skills = skills_gt.get(resume_id, [])
        predicted = match_roles(skills, min_score=0, top_n=10)
        predicted_roles = [match.role for match in predicted]
        relevant_set = {role.lower() for role in relevant_roles}
        hits = sum(1 for role in predicted_roles if role.lower() in relevant_set)
        precision_at_10 = hits / 10.0 if predicted_roles else 0.0
        precisions.append(precision_at_10)

        details.append(
            {
                "resume_id": resume_id,
                "relevant_roles": relevant_roles,
                "predicted_roles": predicted_roles,
                "hits": hits,
                "precision_at_10": round(precision_at_10, 4),
            }
        )

    avg_precision = sum(precisions) / len(precisions) if precisions else 0.0
    result = {
        "samples": len(details),
        "precision_at_10": round(avg_precision, 4),
        "status": "good" if avg_precision >= 0.75 else "needs_improvement",
        "evaluation_type": "ground_truth_role_match",
        "details": details,
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)
    return result


if __name__ == "__main__":
    print(json.dumps(evaluate_matching(), indent=2))
