from src.models.schemas import JobPosting, MatchResult
from src.role_mapping.matcher import RoleMatch
from src.shap_explainer import MatchSHAPExplainer


def test_explain_job_matches_returns_factor_lists():
    explainer = MatchSHAPExplainer()
    posting = JobPosting(
        job_id="job-1",
        title="Data Scientist",
        company="Acme",
        description="Build machine learning systems with Python and SQL.",
        required_skills=["python", "sql", "machine learning"],
        preferred_skills=["docker"],
        experience_level="mid",
    )
    match = MatchResult(
        job=posting,
        overall_score=72.0,
        skill_score=70.0,
        experience_score=80.0,
        semantic_score=0.0,
        matched_required=["python", "sql"],
        matched_preferred=[],
        missing_required=["machine learning"],
    )

    explanations = explainer.explain_job_matches(
        resume_text="Python SQL pandas projects with 3 years experience",
        resume_skills=["python", "sql", "pandas"],
        matches=[match],
        postings=[posting],
    )

    explanation = explanations["job-1"]
    assert explanation["target_type"] == "job"
    assert "summary" in explanation
    assert isinstance(explanation["positive_factors"], list)
    assert isinstance(explanation["negative_factors"], list)


def test_explain_role_matches_returns_role_key():
    explainer = MatchSHAPExplainer()
    role_match = RoleMatch(
        role="Machine Learning Engineer",
        domain="AI/ML",
        description="Build and deploy ML systems.",
        score=68.0,
        core_match_pct=50.0,
        matched_core=["python", "machine learning"],
        matched_optional=["docker"],
        missing_core=["pytorch"],
        total_matched=3,
    )

    explanations = explainer.explain_role_matches(
        resume_text="Python machine learning and Docker projects",
        resume_skills=["python", "machine learning", "docker"],
        role_matches=[role_match],
    )

    assert "Machine Learning Engineer" in explanations
    assert explanations["Machine Learning Engineer"]["target_type"] == "role"
