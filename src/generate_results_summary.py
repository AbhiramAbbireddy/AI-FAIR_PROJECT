"""
Component 13: Master evaluation report generator.
"""
from __future__ import annotations

import json

from src.config.settings import BASE_DIR
from src.evaluate_fairness import evaluate_fairness_metrics
from src.evaluate_matching import evaluate_matching
from src.evaluate_priorities import evaluate_priorities
from src.evaluate_roberta import evaluate_roberta
from src.evaluate_shap import evaluate_shap
from src.evaluate_trends import evaluate_trends


RESULTS_DIR = BASE_DIR / "results"
REPORT_PATH = RESULTS_DIR / "MASTER_EVALUATION_REPORT.md"


def _pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:.1f}%"


def generate_results_summary() -> dict:
    roberta = evaluate_roberta()
    matching = evaluate_matching()
    shap_result = evaluate_shap()
    trends = evaluate_trends()
    priorities = evaluate_priorities()
    fairness = evaluate_fairness_metrics()
    trend_mape = f"{trends['mape']:.2f}%" if trends["mape"] is not None else "N/A"

    report = f"""# Fair-Path Evaluation Report

## 1. Skill Extraction
Precision: {_pct(roberta["precision"])}
Recall: {_pct(roberta["recall"])}
F1-Score: {_pct(roberta["f1_score"])}
Status: {roberta["status"]}

## 2. Job Matching
Precision@10: {_pct(matching["precision_at_10"])}
Status: {matching["status"]}

## 3. SHAP Explainability
Understanding Rate: {_pct(shap_result["understanding_rate"])}
Average Clarity: {shap_result["average_clarity"]:.2f}/5
Status: {shap_result["status"]}
Note: Automated proxy evaluation, not a human user study.

## 4. Trend Forecasting
MAPE: {trend_mape}
Status: {trends["status"]}

## 5. Priority Ranking
Acceptance Rate: {_pct(priorities["acceptance_rate"])}
Average Usefulness: {priorities["average_usefulness"]:.2f}/5
Status: {priorities["status"]}
Note: Automated proxy evaluation, not a human survey.

## 6. Fairness
Gender DPD: {fairness["gender_dpd"]:.4f}
Ethnicity DPD: {fairness["ethnicity_dpd"]:.4f}
Status: {fairness["status"]}

## Overall
Ready for defense if you clearly present which evaluations are ground-truth based and which are automated proxies.
"""

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as file:
        file.write(report)

    summary = {
        "roberta": roberta,
        "matching": matching,
        "shap": shap_result,
        "trends": trends,
        "priorities": priorities,
        "fairness": fairness,
        "report_path": str(REPORT_PATH),
    }
    return summary


if __name__ == "__main__":
    print(json.dumps(generate_results_summary(), indent=2))
