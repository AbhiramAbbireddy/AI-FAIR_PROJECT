import pandas as pd

from src.job_roles_database import JobRoleProfile
from src.temporal_job_dynamics import analyze_role_temporal_dynamics


def test_temporal_job_dynamics_flags_rising_optional_skill():
    jobs_df = pd.DataFrame(
        [
            {
                "title": "Machine Learning Engineer",
                "description": "Build ML services with python and tensorflow",
                "required_skills": "python,machine learning,tensorflow",
                "preferred_skills": "sql",
                "posted_date": "2024-01-15",
            },
            {
                "title": "Machine Learning Engineer",
                "description": "Production ML with python and docker",
                "required_skills": "python,machine learning,tensorflow",
                "preferred_skills": "docker",
                "posted_date": "2024-02-18",
            },
            {
                "title": "Machine Learning Engineer",
                "description": "Deploy ML systems with docker and mlops",
                "required_skills": "python,machine learning,tensorflow,docker",
                "preferred_skills": "mlops",
                "posted_date": "2024-06-03",
            },
            {
                "title": "Machine Learning Engineer",
                "description": "Build and deploy models with docker and mlops",
                "required_skills": "python,machine learning,tensorflow,docker",
                "preferred_skills": "mlops",
                "posted_date": "2024-07-04",
            },
        ]
    )
    role = JobRoleProfile(
        role="Machine Learning Engineer",
        domain="AI/ML",
        core_skills=("python", "machine learning", "tensorflow"),
        optional_skills=("docker", "mlops"),
        description="Builds and deploys machine learning systems.",
        level="Mid",
    )

    result = analyze_role_temporal_dynamics(
        jobs_df,
        role_profile=role,
        user_skills=["python", "machine learning", "tensorflow"],
        current_match_score=78.0,
    )

    assert result is not None
    assert result.jobs_considered >= 4
    assert result.projected_match_score_6m <= 78.0
    assert "docker" in result.rising_requirements
    assert any(signal.skill == "docker" and signal.urgency == "act-now" for signal in result.evolving_skills)
