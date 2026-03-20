import pandas as pd

from src.job_matcher import jobs_df_to_postings, match_resume_to_job, match_resume_to_jobs
from src.models.schemas import JobPosting


def test_match_resume_to_job_without_semantic():
    job = JobPosting(
        job_id="1",
        title="Data Scientist",
        required_skills=["python", "sql", "machine learning"],
        preferred_skills=["docker"],
        description="Build data products with Python and machine learning.",
        experience_level="mid",
    )

    result = match_resume_to_job(
        "Python developer with machine learning and SQL experience.",
        ["python", "sql", "machine learning"],
        job,
        use_semantic=False,
    )

    assert result.overall_score > 0
    assert "python" in result.matched_required
    assert result.skill_score >= 70


def test_match_resume_to_jobs_orders_better_match_first():
    jobs = [
        JobPosting(
            job_id="1",
            title="Backend Developer",
            required_skills=["python", "sql"],
            preferred_skills=["docker"],
            experience_level="mid",
        ),
        JobPosting(
            job_id="2",
            title="Frontend Developer",
            required_skills=["react", "javascript"],
            preferred_skills=["css"],
            experience_level="mid",
        ),
    ]

    results = match_resume_to_jobs(
        "Python backend engineer with SQL and Docker.",
        ["python", "sql", "docker"],
        jobs,
        use_semantic=False,
        top_n=2,
    )

    assert len(results) == 2
    assert results[0].job.title == "Backend Developer"
    assert results[0].overall_score >= results[1].overall_score


def test_jobs_df_to_postings_converts_legacy_dataframe():
    df = pd.DataFrame(
        [
            {
                "job_id": "job-1",
                "title": "ML Engineer",
                "company_name": "Acme",
                "description": "Deploy models",
                "required_skills": "python, machine learning",
                "preferred_skills": "docker, aws",
                "location": "Remote",
                "normalized_salary": 100000,
                "remote_allowed": 1,
                "formatted_experience_level": "mid",
            }
        ]
    )

    postings = jobs_df_to_postings(df)

    assert len(postings) == 1
    assert postings[0].title == "ML Engineer"
    assert postings[0].required_skills == ["python", "machine learning"]
    assert postings[0].remote is True
