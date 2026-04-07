"""
User-facing summary and export helpers for FAIR-PATH.
"""
from __future__ import annotations

from typing import Any

from src.models.schemas import (
    CareerTrajectoryReport,
    ContinuousLearningReport,
    FairnessReport,
    InterviewPrepReport,
    PortfolioReport,
    ResumeParseResult,
)
from src.role_mapping.matcher import RoleMatch


def build_priority_actions(
    *,
    role_matches: list[RoleMatch] | None,
    comprehensive_analysis: dict[str, Any] | None,
    temporal_dynamics: Any | None,
    portfolio_report: PortfolioReport | None,
    interview_prep: InterviewPrepReport | None,
) -> list[str]:
    actions: list[str] = []

    if role_matches:
        top_role = role_matches[0]
        if top_role.missing_core:
            missing = ", ".join(skill.title() for skill in top_role.missing_core[:3])
            actions.append(f"Close the top-role gaps for {top_role.role}: {missing}.")

    ranked_priorities = (comprehensive_analysis or {}).get("ranked_priorities", [])
    if ranked_priorities:
        top_priority = ranked_priorities[0]
        actions.append(
            f"Start with {str(top_priority.get('skill', 'the top priority skill')).title()} because it carries the highest immediate impact."
        )

    if temporal_dynamics is not None and getattr(temporal_dynamics, "rising_requirements", None):
        rising = list(temporal_dynamics.rising_requirements)[:2]
        if rising:
            actions.append(
                f"Act early on market-shifting skills: {', '.join(skill.title() for skill in rising)}."
            )

    if portfolio_report is not None and portfolio_report.weak_skills:
        weak = ", ".join(item.skill.title() for item in portfolio_report.weak_skills[:2])
        actions.append(f"Strengthen portfolio proof for: {weak}.")

    if interview_prep is not None and interview_prep.focus_skills:
        focus = ", ".join(skill.title() for skill in interview_prep.focus_skills[:2])
        actions.append(f"Practice interview answers around: {focus}.")

    deduped: list[str] = []
    seen: set[str] = set()
    for action in actions:
        if action not in seen:
            seen.add(action)
            deduped.append(action)
    return deduped[:5]


def build_executive_summary(
    *,
    resume_profile: ResumeParseResult | None,
    role_matches: list[RoleMatch] | None,
    portfolio_report: PortfolioReport | None,
    interview_prep: InterviewPrepReport | None,
    learning_validation: ContinuousLearningReport | None,
    career_trajectory: CareerTrajectoryReport | None,
    comprehensive_analysis: dict[str, Any] | None,
    temporal_dynamics: Any | None,
    fairness: FairnessReport | None,
) -> dict[str, Any]:
    role_matches = role_matches or []
    top_role = role_matches[0] if role_matches else None
    actions = build_priority_actions(
        role_matches=role_matches,
        comprehensive_analysis=comprehensive_analysis,
        temporal_dynamics=temporal_dynamics,
        portfolio_report=portfolio_report,
        interview_prep=interview_prep,
    )

    summary_lines: list[str] = []
    if top_role is not None:
        summary_lines.append(
            f"Your strongest current fit is {top_role.role} at {top_role.score:.1f}% match."
        )
    if career_trajectory is not None and career_trajectory.recommended_path:
        summary_lines.append(
            f"The strongest long-term upside path is {career_trajectory.recommended_path}."
        )
    if temporal_dynamics is not None:
        summary_lines.append(
            f"Market drift suggests a 6-month projected match of {temporal_dynamics.projected_match_score_6m:.1f}% if rising requirements are ignored."
        )
    if portfolio_report is not None:
        summary_lines.append(
            f"Portfolio evidence is currently {portfolio_report.portfolio_score:.1f}/100."
        )
    if interview_prep is not None:
        summary_lines.append(
            f"Interview readiness is {interview_prep.success_probability:.1f}%."
        )
    if fairness is not None:
        summary_lines.append(
            f"Fairness score is {fairness.score:.1f}/100 with DPD {fairness.demographic_parity_difference:.3f}."
        )

    return {
        "headline": " ".join(summary_lines) if summary_lines else "Run the analysis to generate a complete FAIR-PATH summary.",
        "top_role": top_role.role if top_role else None,
        "top_match_score": top_role.score if top_role else 0.0,
        "experience_years": resume_profile.experience_years if resume_profile else None,
        "actions": actions,
    }


def build_markdown_report(
    *,
    resume_profile: ResumeParseResult | None,
    skills_count: int,
    role_matches: list[RoleMatch] | None,
    portfolio_report: PortfolioReport | None,
    interview_prep: InterviewPrepReport | None,
    learning_validation: ContinuousLearningReport | None,
    career_trajectory: CareerTrajectoryReport | None,
    comprehensive_analysis: dict[str, Any] | None,
    temporal_dynamics: Any | None,
    fairness: FairnessReport | None,
) -> str:
    executive = build_executive_summary(
        resume_profile=resume_profile,
        role_matches=role_matches,
        portfolio_report=portfolio_report,
        interview_prep=interview_prep,
        learning_validation=learning_validation,
        career_trajectory=career_trajectory,
        comprehensive_analysis=comprehensive_analysis,
        temporal_dynamics=temporal_dynamics,
        fairness=fairness,
    )

    role_matches = role_matches or []
    ranked_priorities = (comprehensive_analysis or {}).get("ranked_priorities", [])
    quick_wins = (comprehensive_analysis or {}).get("quick_wins", [])
    lines = [
        "# FAIR-PATH Career Report",
        "",
        "## Executive Summary",
        executive["headline"],
        "",
        "## Resume Snapshot",
        f"- Skills extracted: {skills_count}",
        f"- Experience years: {resume_profile.experience_years if resume_profile and resume_profile.experience_years is not None else 'Not detected'}",
        "",
        "## Top Role Matches",
    ]

    if role_matches:
        for match in role_matches[:5]:
            lines.append(
                f"- {match.role} ({match.domain}) - {match.score:.1f}% match | Missing core: {', '.join(match.missing_core[:4]) or 'None'}"
            )
    else:
        lines.append("- No role matches available")

    lines.extend(["", "## Priority Actions"])
    for action in executive["actions"] or ["-"]:
        lines.append(f"- {action}")

    lines.extend(["", "## Skill Priorities"])
    if ranked_priorities:
        for item in ranked_priorities[:5]:
            lines.append(
                f"- {str(item.get('skill', '')).title()} - {float(item.get('priority_score', 0.0)):.1f}/100"
            )
    else:
        lines.append("- No ranked priorities available")

    lines.extend(["", "## Quick Wins"])
    if quick_wins:
        for item in quick_wins[:3]:
            lines.append(
                f"- {str(item.get('skill', '')).title()} - {float(item.get('priority_score', 0.0)):.1f}/100"
            )
    else:
        lines.append("- No quick wins identified")

    lines.extend(["", "## Portfolio Validation"])
    if portfolio_report is not None:
        lines.append(f"- Portfolio score: {portfolio_report.portfolio_score:.1f}/100")
        if portfolio_report.recommendations:
            for recommendation in portfolio_report.recommendations[:4]:
                lines.append(f"- {recommendation}")
    else:
        lines.append("- Portfolio report unavailable")

    lines.extend(["", "## Interview Preparation"])
    if interview_prep is not None:
        lines.append(f"- Success probability: {interview_prep.success_probability:.1f}%")
        if interview_prep.recommendations:
            for recommendation in interview_prep.recommendations[:4]:
                lines.append(f"- {recommendation}")
    else:
        lines.append("- Interview prep unavailable")

    lines.extend(["", "## Learning Validation"])
    if learning_validation is not None:
        lines.append(f"- Checkpoints: {len(learning_validation.checkpoints)}")
        for checkpoint in learning_validation.checkpoints[:4]:
            lines.append(
                f"- {checkpoint.skill.title()} | {checkpoint.milestone_label} | target {checkpoint.target_score:.0f}%"
            )
    else:
        lines.append("- Learning validation unavailable")

    lines.extend(["", "## Career Trajectory"])
    if career_trajectory is not None and career_trajectory.paths:
        lines.append(f"- Recommended path: {career_trajectory.recommended_path}")
        for path in career_trajectory.paths[:3]:
            lines.append(
                f"- {path.role}: Year 1 {path.salary_year_1_lpa:.1f} LPA | Year 3 {path.salary_year_3_lpa:.1f} LPA | Year 5 {path.salary_year_5_lpa:.1f} LPA | ROI {path.roi_score:.1f}"
            )
    else:
        lines.append("- Career trajectory unavailable")

    lines.extend(["", "## Temporal Dynamics"])
    if temporal_dynamics is not None:
        lines.append(
            f"- Projected 6-month match: {temporal_dynamics.projected_match_score_6m:.1f}%"
        )
        if getattr(temporal_dynamics, "recommendations", None):
            for recommendation in list(temporal_dynamics.recommendations)[:4]:
                lines.append(f"- {recommendation}")
    else:
        lines.append("- Temporal dynamics unavailable")

    lines.extend(["", "## Fairness"])
    if fairness is not None:
        lines.append(f"- Fairness score: {fairness.score:.1f}/100")
        lines.append(f"- Demographic parity difference: {fairness.demographic_parity_difference:.3f}")
        for recommendation in fairness.recommendations[:4]:
            lines.append(f"- {recommendation}")
    else:
        lines.append("- Fairness report unavailable")

    return "\n".join(lines) + "\n"
