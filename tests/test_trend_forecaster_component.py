import pandas as pd

from src.trend_forecaster import (
    compute_current_demand,
    compute_monthly_skill_timeseries,
    compute_time_trends,
    get_skill_trends,
    get_trends_for_skills,
)


def test_compute_current_demand_counts_unique_skills_per_job():
    jobs_df = pd.DataFrame(
        [
            {"required_skills": "python, sql", "preferred_skills": "docker, python"},
            {"required_skills": "python", "preferred_skills": "aws"},
        ]
    )

    demand = compute_current_demand(jobs_df)
    python_row = demand[demand["skill"] == "python"].iloc[0]

    assert int(python_row["job_count"]) == 2


def test_compute_time_trends_detects_growth():
    jobs_df = pd.DataFrame(
        [
            {"posted_date": "2025-01-15", "required_skills": "python", "preferred_skills": ""},
            {"posted_date": "2025-02-10", "required_skills": "python", "preferred_skills": ""},
            {"posted_date": "2025-07-15", "required_skills": "python, docker", "preferred_skills": ""},
            {"posted_date": "2025-08-10", "required_skills": "python, docker", "preferred_skills": ""},
        ]
    )

    trends = compute_time_trends(jobs_df)
    docker_row = trends[trends["skill"] == "docker"].iloc[0]

    assert float(docker_row["growth_pct"]) >= 100.0


def test_get_trends_for_skills_returns_requested_order():
    jobs_df = pd.DataFrame(
        [
            {"posted_date": "2025-01-15", "required_skills": "python", "preferred_skills": "sql"},
            {"posted_date": "2025-02-15", "required_skills": "docker", "preferred_skills": "python"},
            {"posted_date": "2025-03-15", "required_skills": "docker", "preferred_skills": ""},
        ]
    )

    selected = get_trends_for_skills(jobs_df, ["docker", "sql", "unknown"])

    assert [trend.skill for trend in selected] == ["docker", "sql", "unknown"]
    assert selected[-1].forecast_demand == "Unknown"


def test_get_skill_trends_returns_schema_objects():
    jobs_df = pd.DataFrame(
        [
            {"posted_date": "2025-01-15", "required_skills": "python", "preferred_skills": "sql"},
            {"posted_date": "2025-02-15", "required_skills": "docker", "preferred_skills": "python"},
        ]
    )

    trends = get_skill_trends(jobs_df, top_n=5)

    assert trends
    assert hasattr(trends[0], "skill")
