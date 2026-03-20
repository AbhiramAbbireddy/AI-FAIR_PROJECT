from src.priority_ranker import PriorityRanker


def test_priority_score_uses_weighted_factors():
    ranker = PriorityRanker(
        trend_data={
            "docker": {
                "growth_rate": 28.0,
                "trend": "Rising",
                "current_pct": 12.0,
            }
        }
    )

    scored = ranker.calculate_priority_score(
        "docker",
        job_description="Docker is required. Experience with Docker and containerization is essential.",
        category="CRITICAL",
        mention_count=2,
    )

    assert scored["skill"] == "docker"
    assert scored["priority_score"] > 70
    assert scored["breakdown"]["job_importance"] >= 95
    assert scored["breakdown"]["market_demand"] >= 85


def test_rank_missing_skills_for_job_prioritizes_required_skills():
    ranker = PriorityRanker(
        trend_data={
            "docker": {"growth_rate": 30.0, "trend": "Rising", "current_pct": 10.0},
            "graphql": {"growth_rate": 2.0, "trend": "Stable", "current_pct": 4.0},
        }
    )

    ranked = ranker.rank_missing_skills_for_job(
        missing_skills=["graphql", "docker"],
        job_description="Docker is required. GraphQL is nice to have.",
        required_skills=["docker"],
        optional_skills=["graphql"],
    )

    assert ranked[0]["skill"] == "docker"
    assert ranked[0]["category"] == "CRITICAL"
