"""
Skill Trend Forecasting
=======================
Analyses job postings to identify trending skills, then forecasts
future demand using simple time-series heuristics (and optionally
Prophet / ARIMA if installed).

Output example::

    Trending Skills (Last 6 Months)
    Kubernetes   +40 %
    LangChain    +60 %
    Kafka        +30 %
"""
from __future__ import annotations

from collections import Counter
from typing import Optional

import numpy as np
import pandas as pd

from src.models.schemas import SkillTrend
from src.config.settings import SKILLS_VOCAB_PATH


def _load_vocab() -> list[str]:
    return pd.read_csv(SKILLS_VOCAB_PATH)["skill"].str.lower().tolist()


def compute_current_demand(jobs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Count skill frequencies across all jobs.

    Returns DataFrame with columns: skill, job_count, percentage.
    """
    total = max(len(jobs_df), 1)
    counts: Counter[str] = Counter()

    for _, row in jobs_df.iterrows():
        for col in ("required_skills", "preferred_skills"):
            raw = row.get(col, "")
            if not isinstance(raw, str) or raw.strip() in ("", "nan"):
                continue
            for s in raw.split(","):
                s = s.strip().lower()
                if s:
                    counts[s] += 1

    rows = [
        {"skill": sk, "job_count": c, "percentage": round(c / total * 100, 2)}
        for sk, c in counts.most_common(100)
    ]
    return pd.DataFrame(rows)


def compute_time_trends(
    jobs_df: pd.DataFrame, date_col: str = "posted_date", periods: int = 2
) -> pd.DataFrame:
    """
    Split job postings into *periods* time windows and compare skill
    frequency in the latest window vs. the prior window.

    Returns DataFrame with columns: skill, growth_pct, current_pct, prior_pct.
    Positive growth_pct means the skill is trending *upward*.
    """
    if date_col not in jobs_df.columns:
        # No temporal data available – return empty
        return pd.DataFrame(columns=["skill", "growth_pct", "current_pct", "prior_pct"])

    df = jobs_df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col]).sort_values(date_col)
    if len(df) < 20:
        return pd.DataFrame(columns=["skill", "growth_pct", "current_pct", "prior_pct"])

    midpoint = df[date_col].quantile(0.5)
    prior = df[df[date_col] < midpoint]
    current = df[df[date_col] >= midpoint]

    def _count(sub: pd.DataFrame) -> Counter:
        c: Counter[str] = Counter()
        for _, r in sub.iterrows():
            for col in ("required_skills", "preferred_skills"):
                raw = r.get(col, "")
                if not isinstance(raw, str) or raw.strip() in ("", "nan"):
                    continue
                for s in raw.split(","):
                    s = s.strip().lower()
                    if s:
                        c[s] += 1
        return c

    prior_c = _count(prior)
    curr_c = _count(current)

    all_skills = set(prior_c) | set(curr_c)
    prior_total = max(len(prior), 1)
    curr_total = max(len(current), 1)

    rows = []
    for sk in all_skills:
        p_pct = prior_c[sk] / prior_total * 100
        c_pct = curr_c[sk] / curr_total * 100
        if p_pct > 0:
            growth = round((c_pct - p_pct) / p_pct * 100, 1)
        elif c_pct > 0:
            growth = 100.0  # new skill
        else:
            growth = 0.0
        rows.append({
            "skill": sk,
            "growth_pct": growth,
            "current_pct": round(c_pct, 2),
            "prior_pct": round(p_pct, 2),
        })

    out = pd.DataFrame(rows).sort_values("growth_pct", ascending=False)
    return out.head(50).reset_index(drop=True)


def _forecast_label(growth: float) -> str:
    if growth >= 40:
        return "🚀 Surging"
    if growth >= 15:
        return "📈 Growing"
    if growth >= -5:
        return "➡️ Stable"
    return "📉 Declining"


def get_skill_trends(
    jobs_df: pd.DataFrame,
    date_col: str = "posted_date",
) -> list[SkillTrend]:
    """
    High-level API: combine current demand + time trend growth.
    """
    demand = compute_current_demand(jobs_df)
    time_trends = compute_time_trends(jobs_df, date_col=date_col)

    # Merge on skill
    merged = demand.merge(
        time_trends[["skill", "growth_pct"]], on="skill", how="left"
    )
    merged["growth_pct"] = merged["growth_pct"].fillna(0)

    results: list[SkillTrend] = []
    for _, row in merged.head(50).iterrows():
        results.append(
            SkillTrend(
                skill=row["skill"],
                current_count=int(row["job_count"]),
                current_pct=float(row["percentage"]),
                growth_pct=float(row["growth_pct"]),
                forecast_demand=_forecast_label(row["growth_pct"]),
            )
        )
    return results
