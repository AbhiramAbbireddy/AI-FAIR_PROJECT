"""
Temporal job-market dynamics for FAIR-PATH.

This component estimates how a target role's skill requirements are evolving
over time using historical job postings. It focuses on practical signals:

- which target-role skills are strengthening or declining
- which optional skills are on track to become required
- how the user's current match may drift over the next 6-12 months
"""
from __future__ import annotations

from dataclasses import dataclass
import re

import pandas as pd

from src.job_roles_database import JobRoleProfile
from src.skill_extraction.normalizer import normalize_skill


@dataclass(frozen=True, slots=True)
class TemporalSkillSignal:
    skill: str
    skill_type: str
    prior_pct: float
    current_pct: float
    projected_pct: float
    growth_pct: float
    momentum: str
    requirement_status: str
    urgency: str
    recommended_action: str


@dataclass(frozen=True, slots=True)
class RoleTemporalDynamics:
    role: str
    jobs_considered: int
    months_covered: int
    projected_match_score_6m: float
    projected_match_score_12m: float
    risk_delta_6m: float
    summary: str
    evolving_skills: tuple[TemporalSkillSignal, ...]
    rising_requirements: tuple[str, ...]
    declining_requirements: tuple[str, ...]
    recommendations: tuple[str, ...]


def _split_skills(value: object) -> set[str]:
    text = str(value).strip()
    if text in ("", "nan", "None"):
        return set()
    return {normalize_skill(token) for token in text.split(",") if normalize_skill(token)}


def _tokenize_role_text(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9\+\#\.]{3,}", text.lower()) if token not in {"and", "for", "with"}}


def _relevance_score(row: pd.Series, role_profile: JobRoleProfile) -> float:
    title = str(row.get("title", "")).lower()
    description = str(row.get("description", "")).lower()
    combined = f"{title} {description}"

    score = 0.0
    role_name = role_profile.role.lower()
    domain = role_profile.domain.lower()
    role_tokens = _tokenize_role_text(role_name)
    domain_tokens = _tokenize_role_text(domain)

    if role_name and role_name in combined:
        score += 4.0
    if domain and domain in combined:
        score += 1.5

    for token in role_tokens:
        if token in combined:
            score += 0.9
    for token in domain_tokens:
        if token in combined:
            score += 0.5

    posting_skills = _split_skills(row.get("required_skills", "")) | _split_skills(row.get("preferred_skills", ""))
    core_overlap = len(posting_skills & set(role_profile.core_skills))
    optional_overlap = len(posting_skills & set(role_profile.optional_skills))
    score += core_overlap * 0.8
    score += optional_overlap * 0.35
    return score


def _filter_role_jobs(jobs_df: pd.DataFrame, role_profile: JobRoleProfile) -> pd.DataFrame:
    if jobs_df.empty:
        return jobs_df.copy()

    df = jobs_df.copy()
    if "posted_date" not in df.columns:
        return pd.DataFrame(columns=df.columns)

    df["posted_date"] = pd.to_datetime(df["posted_date"], errors="coerce")
    df = df.dropna(subset=["posted_date"]).copy()
    if df.empty:
        return df

    df["relevance_score"] = df.apply(lambda row: _relevance_score(row, role_profile), axis=1)
    filtered = df[df["relevance_score"] >= 2.2].copy()
    if filtered.empty:
        filtered = df.nlargest(min(250, len(df)), "relevance_score").copy()
        filtered = filtered[filtered["relevance_score"] > 0]
    else:
        filtered = filtered.nlargest(min(300, len(filtered)), "relevance_score").copy()
    return filtered


def _build_monthly_skill_presence(role_jobs: pd.DataFrame, target_skills: list[str]) -> pd.DataFrame:
    if role_jobs.empty:
        return pd.DataFrame(columns=["month", "skill", "job_pct"])

    rows: list[dict[str, object]] = []
    role_jobs = role_jobs.copy()
    role_jobs["month"] = role_jobs["posted_date"].dt.to_period("M").astype(str)

    for month, month_df in role_jobs.groupby("month"):
        total_jobs = max(len(month_df), 1)
        for skill in target_skills:
            count = 0
            for _, row in month_df.iterrows():
                skills = _split_skills(row.get("required_skills", "")) | _split_skills(row.get("preferred_skills", ""))
                if skill in skills:
                    count += 1
            rows.append(
                {
                    "month": month,
                    "skill": skill,
                    "job_pct": count / total_jobs * 100.0,
                }
            )

    return pd.DataFrame(rows).sort_values(["skill", "month"]).reset_index(drop=True)


def _project_pct(values: list[float], months_ahead: int) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return round(values[-1], 1)

    x = list(range(len(values)))
    x_mean = sum(x) / len(x)
    y_mean = sum(values) / len(values)
    numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, values))
    denominator = sum((xi - x_mean) ** 2 for xi in x)
    slope = numerator / denominator if denominator else 0.0
    projection = values[-1] + slope * months_ahead
    return round(max(0.0, min(100.0, projection)), 1)


def _growth(prior_pct: float, current_pct: float) -> float:
    if prior_pct > 0:
        return round((current_pct - prior_pct) / prior_pct * 100.0, 1)
    if current_pct > 0:
        return 100.0
    return 0.0


def _momentum_label(growth_pct: float) -> str:
    if growth_pct >= 20:
        return "accelerating"
    if growth_pct >= 5:
        return "rising"
    if growth_pct <= -15:
        return "falling"
    return "stable"


def _requirement_status(skill_type: str, current_pct: float, projected_pct: float, growth_pct: float) -> str:
    if skill_type == "core":
        if current_pct >= 55 or projected_pct >= 65:
            return "required-now"
        if growth_pct >= 15:
            return "strengthening"
        if growth_pct <= -15:
            return "softening"
        return "steady-core"

    if projected_pct >= 45 and growth_pct >= 15:
        return "likely-required"
    if growth_pct >= 12:
        return "emerging"
    if growth_pct <= -15:
        return "declining"
    return "steady-optional"


def _urgency(skill: str, user_skills: set[str], status: str, skill_type: str) -> str:
    if skill in user_skills:
        return "covered"
    if status in {"likely-required", "required-now", "strengthening"}:
        return "act-now"
    if skill_type == "core":
        return "important"
    if status == "emerging":
        return "watchlist"
    return "later"


def _recommended_action(skill: str, urgency: str, status: str) -> str:
    skill_name = skill.title()
    if urgency == "covered":
        return f"You already cover {skill_name}; keep it visible in projects and interview prep."
    if urgency == "act-now":
        return f"Prioritize {skill_name} now because this signal is moving toward a required expectation."
    if urgency == "important":
        return f"Plan {skill_name} soon because it remains part of the role's stable core."
    if status == "declining":
        return f"De-prioritize {skill_name} unless your target company explicitly asks for it."
    return f"Track {skill_name} and learn it after the current highest-impact gaps."


def analyze_role_temporal_dynamics(
    jobs_df: pd.DataFrame,
    role_profile: JobRoleProfile,
    user_skills: list[str],
    current_match_score: float,
) -> RoleTemporalDynamics | None:
    if jobs_df.empty:
        return None

    role_jobs = _filter_role_jobs(jobs_df, role_profile)
    if role_jobs.empty:
        return None

    target_skills = list(dict.fromkeys([*role_profile.core_skills, *role_profile.optional_skills]))
    if not target_skills:
        return None

    monthly = _build_monthly_skill_presence(role_jobs, target_skills)
    if monthly.empty:
        return None

    months = sorted(monthly["month"].unique())
    if not months:
        return None

    split_idx = max(len(months) // 2, 1)
    prior_months = set(months[:split_idx])
    current_months = set(months[split_idx:]) or set(months[-1:])

    normalized_user_skills = {normalize_skill(skill) for skill in user_skills if normalize_skill(skill)}
    signals: list[TemporalSkillSignal] = []

    for skill in target_skills:
        skill_rows = monthly[monthly["skill"] == skill].sort_values("month")
        values = [float(value) for value in skill_rows["job_pct"].tolist()]
        if not values:
            continue

        prior_rows = skill_rows[skill_rows["month"].isin(prior_months)]
        current_rows = skill_rows[skill_rows["month"].isin(current_months)]
        prior_pct = round(float(prior_rows["job_pct"].mean()) if not prior_rows.empty else values[0], 1)
        current_pct = round(float(current_rows["job_pct"].mean()) if not current_rows.empty else values[-1], 1)
        projected_pct = _project_pct(values, months_ahead=6)
        growth_pct = _growth(prior_pct, current_pct)
        skill_type = "core" if skill in role_profile.core_skills else "optional"
        momentum = _momentum_label(growth_pct)
        requirement_status = _requirement_status(skill_type, current_pct, projected_pct, growth_pct)
        urgency = _urgency(skill, normalized_user_skills, requirement_status, skill_type)
        signals.append(
            TemporalSkillSignal(
                skill=skill,
                skill_type=skill_type,
                prior_pct=prior_pct,
                current_pct=current_pct,
                projected_pct=projected_pct,
                growth_pct=growth_pct,
                momentum=momentum,
                requirement_status=requirement_status,
                urgency=urgency,
                recommended_action=_recommended_action(skill, urgency, requirement_status),
            )
        )

    signals.sort(
        key=lambda item: (
            0 if item.urgency == "act-now" else 1 if item.urgency == "important" else 2,
            -item.projected_pct,
            -item.growth_pct,
        )
    )

    pressure_6m = 0.0
    pressure_12m = 0.0
    for signal in signals:
        if signal.skill in normalized_user_skills:
            continue
        weight = 1.0 if signal.skill_type == "core" else 0.6
        if signal.requirement_status in {"required-now", "likely-required", "strengthening"}:
            pressure_6m += weight * max(0.0, signal.projected_pct - signal.current_pct) / 6.5
            pressure_12m += weight * max(0.0, signal.projected_pct - signal.prior_pct) / 5.0
        elif signal.requirement_status == "steady-core":
            pressure_6m += weight * 1.2
            pressure_12m += weight * 1.6

    projected_match_score_6m = round(max(0.0, min(100.0, current_match_score - pressure_6m)), 1)
    projected_match_score_12m = round(max(0.0, min(100.0, current_match_score - pressure_12m)), 1)
    risk_delta_6m = round(projected_match_score_6m - current_match_score, 1)

    rising_requirements = tuple(
        signal.skill
        for signal in signals
        if signal.requirement_status in {"likely-required", "strengthening", "required-now"}
    )
    declining_requirements = tuple(
        signal.skill for signal in signals if signal.requirement_status in {"declining", "softening"}
    )

    recommendations: list[str] = []
    for signal in signals[:4]:
        if signal.urgency in {"act-now", "important"}:
            recommendations.append(signal.recommended_action)
    if not recommendations:
        recommendations.append(
            f"The {role_profile.role} skill profile looks stable right now. Focus on the current core gaps before chasing newer optional tools."
        )

    top_signal = signals[0] if signals else None
    summary = (
        f"For {role_profile.role}, the market sample covers {len(months)} months and {len(role_jobs)} relevant postings. "
        f"The role is currently most sensitive to {top_signal.skill if top_signal else 'core skills'}, "
        f"and your projected match could move from {current_match_score:.1f}% to {projected_match_score_6m:.1f}% in about 6 months "
        f"if rising requirements are not addressed."
    )

    return RoleTemporalDynamics(
        role=role_profile.role,
        jobs_considered=int(len(role_jobs)),
        months_covered=len(months),
        projected_match_score_6m=projected_match_score_6m,
        projected_match_score_12m=projected_match_score_12m,
        risk_delta_6m=risk_delta_6m,
        summary=summary,
        evolving_skills=tuple(signals),
        rising_requirements=rising_requirements,
        declining_requirements=declining_requirements,
        recommendations=tuple(recommendations),
    )
