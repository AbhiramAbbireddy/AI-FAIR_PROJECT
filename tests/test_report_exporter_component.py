from src.models.schemas import FairnessReport, PortfolioReport, ResumeParseResult
from src.report_exporter import build_executive_summary, build_markdown_report
from src.role_mapping.matcher import RoleMatch


def test_report_exporter_builds_summary_and_markdown():
    resume = ResumeParseResult(text="sample", email="test@example.com", phone="1234567890", experience_years=2)
    roles = [
        RoleMatch(
            role="LLM Engineer",
            domain="AI/ML",
            description="Builds llm systems",
            score=74.0,
            core_match_pct=70.0,
            matched_core=["python"],
            matched_optional=["langchain"],
            missing_core=["docker", "rag"],
            total_matched=2,
            proficiency_alignment=72.0,
        )
    ]
    portfolio = PortfolioReport(portfolio_score=68.0)
    fairness = FairnessReport(score=95.0, demographic_parity_difference=0.02)

    summary = build_executive_summary(
        resume_profile=resume,
        role_matches=roles,
        portfolio_report=portfolio,
        interview_prep=None,
        learning_validation=None,
        career_trajectory=None,
        comprehensive_analysis={"ranked_priorities": [{"skill": "docker", "priority_score": 91.0}]},
        temporal_dynamics=None,
        fairness=fairness,
    )
    report = build_markdown_report(
        resume_profile=resume,
        skills_count=8,
        role_matches=roles,
        portfolio_report=portfolio,
        interview_prep=None,
        learning_validation=None,
        career_trajectory=None,
        comprehensive_analysis={"ranked_priorities": [{"skill": "docker", "priority_score": 91.0}]},
        temporal_dynamics=None,
        fairness=fairness,
    )

    assert summary["top_role"] == "LLM Engineer"
    assert "LLM Engineer" in report
    assert "Priority Actions" in report
