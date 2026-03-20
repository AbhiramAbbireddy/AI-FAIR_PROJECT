"""
Evaluation 4: Trend forecasting backtest.
"""
from __future__ import annotations

import json

import pandas as pd

from src.config.settings import JOBS_PARSED_PATH, BASE_DIR
from src.trend_forecaster import compute_monthly_skill_timeseries


RESULTS_PATH = BASE_DIR / "results" / "trend_forecasting_mape.json"


def evaluate_trends() -> dict:
    jobs_df = pd.read_csv(JOBS_PARSED_PATH)
    monthly = compute_monthly_skill_timeseries(jobs_df)
    monthly["month_dt"] = pd.to_datetime(monthly["month"] + "-01", errors="coerce")
    monthly = monthly.dropna(subset=["month_dt"])

    if monthly.empty or monthly["month"].nunique() < 4:
        result = {
            "samples": 0,
            "mape": None,
            "status": "insufficient_data",
            "evaluation_type": "monthly_backtest",
            "details": [],
        }
    else:
        cutoff = monthly["month_dt"].max() - pd.DateOffset(months=2)
        train = monthly[monthly["month_dt"] < cutoff]
        test = monthly[monthly["month_dt"] >= cutoff]

        details = []
        absolute_percentage_errors = []
        for skill, group in test.groupby("skill"):
            history = train[train["skill"] == skill].sort_values("month_dt")
            if history.empty:
                continue
            baseline = float(history["job_count"].tail(min(3, len(history))).mean())
            for _, row in group.iterrows():
                actual = float(row["job_count"])
                predicted = baseline
                ape = abs(actual - predicted) / actual * 100.0 if actual else 0.0
                absolute_percentage_errors.append(ape)
                details.append(
                    {
                        "skill": skill,
                        "month": row["month"],
                        "actual": actual,
                        "predicted": round(predicted, 2),
                        "ape": round(ape, 2),
                    }
                )

        mape = sum(absolute_percentage_errors) / len(absolute_percentage_errors) if absolute_percentage_errors else None
        result = {
            "samples": len(details),
            "mape": round(mape, 4) if mape is not None else None,
            "status": "acceptable" if mape is not None and mape < 20 else "needs_improvement",
            "evaluation_type": "monthly_backtest",
            "details": details[:100],
        }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)
    return result


if __name__ == "__main__":
    print(json.dumps(evaluate_trends(), indent=2))
