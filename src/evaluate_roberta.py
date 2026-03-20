"""
Evaluation 1: Skill extraction accuracy.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.config.settings import BASE_DIR
from src.skill_extractor import extract_skill_names


GROUND_TRUTH_PATH = BASE_DIR / "data" / "ground_truth_skills.json"
RESULTS_PATH = BASE_DIR / "results" / "roberta_accuracy.json"


def _build_resume_text(skills: list[str]) -> str:
    return (
        "Experienced professional with hands-on work in "
        + ", ".join(skills)
        + ". Built projects, delivered production work, and collaborated across teams."
    )


def evaluate_roberta() -> dict:
    with open(GROUND_TRUTH_PATH, "r", encoding="utf-8") as file:
        ground_truth = json.load(file)

    total_correct = 0
    total_predicted = 0
    total_actual = 0
    per_resume = []

    for resume_id, skills in ground_truth.items():
        actual = {skill.lower() for skill in skills}
        predicted = set(extract_skill_names(_build_resume_text(skills), use_ner=True))

        correct = len(actual & predicted)
        total_correct += correct
        total_predicted += len(predicted)
        total_actual += len(actual)

        per_resume.append(
            {
                "resume_id": resume_id,
                "actual_skills": sorted(actual),
                "predicted_skills": sorted(predicted),
                "correct": correct,
            }
        )

    precision = total_correct / total_predicted if total_predicted else 0.0
    recall = total_correct / total_actual if total_actual else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    result = {
        "samples": len(ground_truth),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "status": "acceptable" if f1 >= 0.8 else "needs_improvement",
        "evaluation_type": "ground_truth_skill_set",
        "details": per_resume,
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)
    return result


if __name__ == "__main__":
    print(json.dumps(evaluate_roberta(), indent=2))
