"""
Career trajectory simulation for FAIR-PATH.

Provides a practical forward-looking view of the top candidate roles:
- estimated readiness after planned learning
- 1/3/5 year salary trajectory
- risk and ROI comparison across role paths
"""
from __future__ import annotations

from dataclasses import dataclass

from src.models.schemas import CareerTrajectoryPath, CareerTrajectoryReport, SkillTrend
from src.role_mapping.matcher import RoleMatch


_DOMAIN_BASE_SALARY_LPA = {
    "ai/ml": 10.5,
    "data engineering": 9.0,
    "software engineering": 8.0,
    "cloud/devops": 9.5,
    "cybersecurity": 9.0,
    "data science": 9.5,
    "product": 8.5,
    "general": 7.5,
}


def _domain_base_salary(domain: str) -> float:
    domain_key = (domain or "general").strip().lower()
    return _DOMAIN_BASE_SALARY_LPA.get(domain_key, _DOMAIN_BASE_SALARY_LPA["general"])


def _role_growth_bonus(role_name: str) -> float:
    role = role_name.lower()
    bonus = 0.0
    if any(token in role for token in ["llm", "generative ai", "ml", "ai"]):
        bonus += 5.0
    if any(token in role for token in ["engineer", "architect"]):
        bonus += 2.0
    if "analyst" in role:
        bonus -= 1.0
    return bonus


def _trend_pressure(missing_skills: list[str], trends: list[SkillTrend]) -> float:
    trend_lookup = {trend.skill.lower(): trend for trend in trends}
    score = 0.0
    for skill in missing_skills[:5]:
        trend = trend_lookup.get(skill.lower())
        if trend is None:
            continue
        score += max(-10.0, min(25.0, trend.growth_pct)) / 10.0
    return score


def _risk_label(success_probability: float) -> str:
    if success_probability >= 78:
        return "Low"
    if success_probability >= 60:
        return "Moderate"
    return "High"


def _salary_projection(base_lpa: float, annual_growth_pct: float, years: int) -> float:
    salary = base_lpa
    for _ in range(years):
        salary *= 1 + annual_growth_pct / 100.0
    return round(salary, 1)


def simulate_career_trajectories(
    role_matches: list[RoleMatch],
    trends: list[SkillTrend],
    current_experience_years: int | None = None,
) -> CareerTrajectoryReport:
    if not role_matches:
        return CareerTrajectoryReport(
            summary="No role matches were available to simulate future trajectories.",
            recommended_path="",
            paths=[],
            source_status="heuristic",
        )

    experience_years = max(0, int(current_experience_years or 0))
    simulated_paths: list[CareerTrajectoryPath] = []

    for match in role_matches[:4]:
        base_salary = _domain_base_salary(match.domain)
        base_salary += min(experience_years, 5) * 0.8
        readiness_bonus = match.score / 20.0
        market_bonus = _role_growth_bonus(match.role)
        pressure_bonus = _trend_pressure(match.missing_core, trends)
        annual_growth_pct = max(6.0, 10.0 + market_bonus + pressure_bonus)

        missing_penalty = min(len(match.missing_core) * 2.5, 15.0)
        success_probability = round(max(30.0, min(92.0, match.score + readiness_bonus - missing_penalty + pressure_bonus * 2.0)), 1)
        projected_match = round(min(96.0, match.score + max(8.0, 18.0 - len(match.missing_core) * 1.5)), 1)

        year_1 = _salary_projection(base_salary + readiness_bonus, annual_growth_pct, 1)
        year_3 = _salary_projection(base_salary + readiness_bonus + 1.0, annual_growth_pct + 1.5, 3)
        year_5 = _salary_projection(base_salary + readiness_bonus + 2.0, annual_growth_pct + 2.5, 5)

        roi_score = round(
            max(10.0, min(100.0, projected_match * 0.45 + success_probability * 0.25 + year_5 * 2.2 - len(match.missing_core) * 4.0)),
            1,
        )
        risk_level = _risk_label(success_probability)

        recommendation = (
            f"{match.role} has a {success_probability:.0f}% transition probability with a projected {year_5:.1f} LPA 5-year outcome. "
            f"Focus first on {', '.join(skill.title() for skill in match.missing_core[:3]) or 'portfolio depth'} to accelerate the path."
        )

        simulated_paths.append(
            CareerTrajectoryPath(
                role=match.role,
                domain=match.domain,
                current_match_score=match.score,
                projected_match_after_learning=projected_match,
                salary_year_1_lpa=year_1,
                salary_year_3_lpa=year_3,
                salary_year_5_lpa=year_5,
                growth_rate_pct=round(annual_growth_pct, 1),
                success_probability=success_probability,
                risk_level=risk_level,
                roi_score=roi_score,
                top_missing_skills=match.missing_core[:5],
                recommendation=recommendation,
            )
        )

    simulated_paths.sort(key=lambda item: (-item.roi_score, -item.salary_year_5_lpa, -item.success_probability))
    recommended = simulated_paths[0].role if simulated_paths else ""
    summary = (
        f"Simulated {len(simulated_paths)} role paths using current match strength, missing skills, and market momentum. "
        f"The highest-upside path right now is {recommended}."
    )

    return CareerTrajectoryReport(
        summary=summary,
        recommended_path=recommended,
        paths=simulated_paths,
        source_status="heuristic",
    )
