"""
Evaluation 5: Priority ranking quality proxy.

Uses consistency checks instead of human acceptance responses.
"""
from __future__ import annotations

import json

from src.config.settings import BASE_DIR
from src.priority_ranker import PriorityRanker


RESULTS_PATH = BASE_DIR / "results" / "priority_acceptance.json"

SCENARIOS = [
    {
        "name": "ml_engineer",
        "missing_skills": ["docker", "pytorch", "jquery"],
        "required_skills": ["docker", "pytorch"],
        "optional_skills": ["jquery"],
        "job_description": "Docker and PyTorch are required for this ML engineer role. jQuery is a nice to have.",
        "trend_data": {
            "docker": {"growth_rate": 28, "trend": "Rising", "current_pct": 12},
            "pytorch": {"growth_rate": 24, "trend": "Rising", "current_pct": 9},
            "jquery": {"growth_rate": -12, "trend": "Declining", "current_pct": 3},
        },
        "expected_top": {"docker", "pytorch"},
    },
    {
        "name": "frontend",
        "missing_skills": ["typescript", "react", "perl"],
        "required_skills": ["typescript", "react"],
        "optional_skills": ["perl"],
        "job_description": "React and TypeScript are essential. Perl is optional legacy support.",
        "trend_data": {
            "typescript": {"growth_rate": 18, "trend": "Rising", "current_pct": 10},
            "react": {"growth_rate": 14, "trend": "Stable", "current_pct": 16},
            "perl": {"growth_rate": -15, "trend": "Declining", "current_pct": 1},
        },
        "expected_top": {"typescript", "react"},
    },
]


def evaluate_priorities() -> dict:
    accepted = 0
    usefulness_scores: list[float] = []
    details = []

    for scenario in SCENARIOS:
        ranker = PriorityRanker(trend_data=scenario["trend_data"])
        ranked = ranker.rank_missing_skills_for_job(
            missing_skills=scenario["missing_skills"],
            job_description=scenario["job_description"],
            required_skills=scenario["required_skills"],
            optional_skills=scenario["optional_skills"],
        )

        top_two = {item["skill"] for item in ranked[:2]}
        follows_expectation = top_two == scenario["expected_top"]
        accepted += 1 if follows_expectation else 0
        usefulness = 5.0 if follows_expectation else 3.0
        usefulness_scores.append(usefulness)

        details.append(
            {
                "scenario": scenario["name"],
                "top_ranked": [item["skill"] for item in ranked[:3]],
                "accepted_proxy": follows_expectation,
                "usefulness_proxy": usefulness,
            }
        )

    acceptance_rate = accepted / len(SCENARIOS) if SCENARIOS else 0.0
    average_usefulness = sum(usefulness_scores) / len(usefulness_scores) if usefulness_scores else 0.0
    result = {
        "samples": len(SCENARIOS),
        "acceptance_rate": round(acceptance_rate, 4),
        "average_usefulness": round(average_usefulness, 4),
        "status": "meets_proxy_target" if acceptance_rate >= 0.85 and average_usefulness >= 4.0 else "needs_review",
        "evaluation_type": "automated_priority_proxy",
        "details": details,
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)
    return result


if __name__ == "__main__":
    print(json.dumps(evaluate_priorities(), indent=2))
