"""
Canonical skill trend forecasting component for FAIR-PATH.

This module turns parsed job data into practical market signals:
- current demand by skill
- recent growth/decline based on monthly windows
- user-focused trend lookup for selected skills

It intentionally keeps the public return type compatible with the existing
`SkillTrend` schema while centralising the logic in one top-level component.
"""
from __future__ import annotations

from collections import Counter

import pandas as pd

from src.models.schemas import SkillTrend


def _split_skills(value: object) -> list[str]:
    text = str(value).strip()
    if text in ("", "nan", "None"):
        return []
    return [token.strip().lower() for token in text.split(",") if token.strip()]


def compute_current_demand(jobs_df: pd.DataFrame) -> pd.DataFrame:
    total_jobs = max(len(jobs_df), 1)
    counts: Counter[str] = Counter()

    for _, row in jobs_df.iterrows():
        seen_in_job: set[str] = set()
        for column in ("required_skills", "preferred_skills"):
            for skill in _split_skills(row.get(column, "")):
                seen_in_job.add(skill)
        for skill in seen_in_job:
            counts[skill] += 1

    return pd.DataFrame(
        [
            {
                "skill": skill,
                "job_count": count,
                "percentage": round(count / total_jobs * 100.0, 2),
            }
            for skill, count in counts.most_common()
        ]
    )


def compute_monthly_skill_timeseries(
    jobs_df: pd.DataFrame,
    *,
    date_col: str = "posted_date",
) -> pd.DataFrame:
    if date_col not in jobs_df.columns:
        return pd.DataFrame(columns=["month", "skill", "job_count"])

    df = jobs_df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])
    if df.empty:
        return pd.DataFrame(columns=["month", "skill", "job_count"])

    df["month"] = df[date_col].dt.to_period("M").astype(str)
    rows: list[dict[str, object]] = []
    for _, row in df.iterrows():
        seen_in_job: set[str] = set()
        for column in ("required_skills", "preferred_skills"):
            for skill in _split_skills(row.get(column, "")):
                seen_in_job.add(skill)
        for skill in seen_in_job:
            rows.append({"month": row["month"], "skill": skill, "job_count": 1})

    if not rows:
        return pd.DataFrame(columns=["month", "skill", "job_count"])

    monthly = (
        pd.DataFrame(rows)
        .groupby(["month", "skill"], as_index=False)["job_count"]
        .sum()
        .sort_values(["month", "job_count"], ascending=[True, False])
    )
    return monthly


def compute_time_trends(
    jobs_df: pd.DataFrame,
    *,
    date_col: str = "posted_date",
    recent_months: int = 6,
) -> pd.DataFrame:
    monthly = compute_monthly_skill_timeseries(jobs_df, date_col=date_col)
    if monthly.empty:
        return pd.DataFrame(columns=["skill", "growth_pct", "current_pct", "prior_pct", "recent_count", "prior_count"])

    month_order = sorted(monthly["month"].unique())
    if len(month_order) < 2:
        return pd.DataFrame(columns=["skill", "growth_pct", "current_pct", "prior_pct", "recent_count", "prior_count"])

    recent_bucket = set(month_order[-recent_months:])
    prior_bucket = set(month_order[:-recent_months] if len(month_order) > recent_months else month_order[:-1])
    if not prior_bucket:
        midpoint = max(len(month_order) // 2, 1)
        prior_bucket = set(month_order[:midpoint])
        recent_bucket = set(month_order[midpoint:])

    monthly_totals = monthly.groupby("month", as_index=False)["job_count"].sum()
    total_recent_mentions = int(monthly_totals[monthly_totals["month"].isin(recent_bucket)]["job_count"].sum())
    total_prior_mentions = int(monthly_totals[monthly_totals["month"].isin(prior_bucket)]["job_count"].sum())
    total_recent_mentions = max(total_recent_mentions, 1)
    total_prior_mentions = max(total_prior_mentions, 1)

    recent_counts = (
        monthly[monthly["month"].isin(recent_bucket)]
        .groupby("skill", as_index=False)["job_count"]
        .sum()
        .rename(columns={"job_count": "recent_count"})
    )
    prior_counts = (
        monthly[monthly["month"].isin(prior_bucket)]
        .groupby("skill", as_index=False)["job_count"]
        .sum()
        .rename(columns={"job_count": "prior_count"})
    )

    merged = recent_counts.merge(prior_counts, on="skill", how="outer").fillna(0)
    merged["recent_count"] = merged["recent_count"].astype(int)
    merged["prior_count"] = merged["prior_count"].astype(int)
    merged["current_pct"] = merged["recent_count"] / total_recent_mentions * 100.0
    merged["prior_pct"] = merged["prior_count"] / total_prior_mentions * 100.0

    def _growth(row: pd.Series) -> float:
        prior_pct = float(row["prior_pct"])
        current_pct = float(row["current_pct"])
        if prior_pct > 0:
            return round((current_pct - prior_pct) / prior_pct * 100.0, 1)
        if current_pct > 0:
            return 100.0
        return 0.0

    merged["growth_pct"] = merged.apply(_growth, axis=1)
    return merged.sort_values(["growth_pct", "recent_count"], ascending=[False, False]).reset_index(drop=True)


def _forecast_label(growth_pct: float) -> str:
    if growth_pct >= 25:
        return "Rising"
    if growth_pct >= -5:
        return "Stable"
    return "Declining"


def _to_skill_trends(merged: pd.DataFrame, demand: pd.DataFrame) -> list[SkillTrend]:
    if demand.empty:
        return []

    enriched = demand.merge(
        merged[["skill", "growth_pct"]] if not merged.empty else pd.DataFrame(columns=["skill", "growth_pct"]),
        on="skill",
        how="left",
    )
    enriched["growth_pct"] = enriched["growth_pct"].fillna(0.0)

    return [
        SkillTrend(
            skill=row["skill"],
            current_count=int(row["job_count"]),
            current_pct=float(row["percentage"]),
            growth_pct=float(row["growth_pct"]),
            forecast_demand=_forecast_label(float(row["growth_pct"])),
        )
        for _, row in enriched.iterrows()
    ]


def get_skill_trends(
    jobs_df: pd.DataFrame,
    *,
    date_col: str = "posted_date",
    top_n: int = 50,
) -> list[SkillTrend]:
    if jobs_df.empty:
        return []

    demand = compute_current_demand(jobs_df)
    trends = compute_time_trends(jobs_df, date_col=date_col)
    skill_trends = _to_skill_trends(trends, demand)
    return skill_trends[:top_n]


def get_trends_for_skills(
    jobs_df: pd.DataFrame,
    skills: list[str],
    *,
    date_col: str = "posted_date",
) -> list[SkillTrend]:
    if jobs_df.empty or not skills:
        return []

    lookup = {trend.skill.lower(): trend for trend in get_skill_trends(jobs_df, date_col=date_col, top_n=500)}
    results: list[SkillTrend] = []
    for skill in dict.fromkeys(skill.lower().strip() for skill in skills if skill.strip()):
        trend = lookup.get(skill)
        if trend is None:
            results.append(
                SkillTrend(
                    skill=skill,
                    current_count=0,
                    current_pct=0.0,
                    growth_pct=0.0,
                    forecast_demand="Unknown",
                )
            )
        else:
            results.append(trend)
    return results
