from src.llm_learning_path_generator import generate_learning_path


def test_generate_learning_path_returns_milestones_from_missing_skills():
    roadmap = generate_learning_path(
        current_skills=["python", "sql"],
        missing_skills=["docker", "pytorch"],
        priority_rankings={"docker": 91.1, "pytorch": 87.5},
        match_score=75.0,
        target_role="Machine Learning Engineer",
        use_cache=False,
        api_key=None,
    )

    assert "milestones" in roadmap
    assert roadmap["milestones"]
    milestone_skills = [item["skill"] for item in roadmap["milestones"]]
    assert "docker" in milestone_skills
    assert "pytorch" in milestone_skills
