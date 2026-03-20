"""
Evaluation 6: Fairness metrics using synthetic demographic variants.
"""
from __future__ import annotations

import json
from collections import defaultdict

from src.config.settings import BASE_DIR
from src.fairness_evaluator import evaluate_fairness


DATA_PATH = BASE_DIR / "data" / "fairness_test_set.json"
RESULTS_PATH = BASE_DIR / "results" / "fairness_evaluation.json"


def _average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _dpd(group_scores: dict[str, list[float]]) -> float:
    averages = [_average(scores) for scores in group_scores.values() if scores]
    if not averages:
        return 0.0
    return max(averages) - min(averages)


def evaluate_fairness_metrics() -> dict:
    with open(DATA_PATH, "r", encoding="utf-8") as file:
        fairness_set = json.load(file)

    gender_scores: dict[str, list[float]] = defaultdict(list)
    origin_scores: dict[str, list[float]] = defaultdict(list)
    details = []

    for resume_id, payload in fairness_set.items():
        report = evaluate_fairness(payload["text"])
        gender_scores[payload.get("demographic_group", "Unknown")].append(report.score)
        origin_scores[payload.get("name_origin", "Unknown")].append(report.score)
        details.append(
            {
                "resume_id": resume_id,
                "group": payload.get("demographic_group"),
                "origin": payload.get("name_origin"),
                "score": report.score,
                "mitigated_score": report.mitigated_score,
            }
        )

    gender_dpd = _dpd(gender_scores) / 100.0
    ethnicity_dpd = _dpd(origin_scores) / 100.0

    result = {
        "samples": len(details),
        "gender_dpd": round(gender_dpd, 4),
        "ethnicity_dpd": round(ethnicity_dpd, 4),
        "status": "fair" if max(gender_dpd, ethnicity_dpd) < 0.1 else "needs_improvement",
        "evaluation_type": "synthetic_resume_fairness_set",
        "details": details,
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)
    return result


if __name__ == "__main__":
    print(json.dumps(evaluate_fairness_metrics(), indent=2))
