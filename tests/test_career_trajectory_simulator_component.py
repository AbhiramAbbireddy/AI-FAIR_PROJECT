from src.career_trajectory_simulator import simulate_career_trajectories
from src.models.schemas import SkillTrend
from src.role_mapping.matcher import RoleMatch


def test_simulate_career_trajectories_returns_ranked_paths():
    role_matches = [
        RoleMatch(
            role="LLM Engineer",
            domain="AI/ML",
            description="Builds llm systems.",
            score=72.0,
            core_match_pct=68.0,
            matched_core=["python", "llm"],
            matched_optional=["langchain"],
            missing_core=["docker", "rag"],
            total_matched=3,
            proficiency_alignment=70.0,
        ),
        RoleMatch(
            role="Frontend Developer",
            domain="Software Engineering",
            description="Builds user interfaces.",
            score=61.0,
            core_match_pct=60.0,
            matched_core=["javascript"],
            matched_optional=["react"],
            missing_core=["typescript"],
            total_matched=2,
            proficiency_alignment=60.0,
        ),
    ]
    trends = [
        SkillTrend(skill="docker", current_count=50, current_pct=20.0, growth_pct=18.0, forecast_demand="Rising"),
        SkillTrend(skill="rag", current_count=35, current_pct=15.0, growth_pct=28.0, forecast_demand="Rising"),
        SkillTrend(skill="typescript", current_count=80, current_pct=30.0, growth_pct=6.0, forecast_demand="Stable"),
    ]

    report = simulate_career_trajectories(role_matches, trends, current_experience_years=1)

    assert report.paths
    assert report.recommended_path == report.paths[0].role
    assert report.paths[0].salary_year_5_lpa >= report.paths[0].salary_year_1_lpa
    assert report.paths[0].roi_score >= report.paths[-1].roi_score
