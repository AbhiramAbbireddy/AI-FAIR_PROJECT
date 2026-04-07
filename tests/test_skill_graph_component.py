from src.skill_graph import SkillGraphAnalyzer


def test_skill_graph_identifies_bottlenecks_and_paths():
    analyzer = SkillGraphAnalyzer()
    result = analyzer.analyze(
        known_skills=["python", "sql"],
        missing_skills=["fastapi", "docker", "pytorch"],
        target_role="ML Engineer",
    )

    assert "dependency_paths" in result
    assert "bottlenecks" in result
    assert "summary" in result
    assert isinstance(result["dependency_paths"], list)
    assert isinstance(result["bottlenecks"], list)


def test_skill_graph_detects_substitute_matches():
    analyzer = SkillGraphAnalyzer()
    result = analyzer.analyze(
        known_skills=["tensorflow"],
        missing_skills=["pytorch"],
        target_role="Machine Learning Engineer",
    )

    substitutes = result.get("substitute_matches", [])
    assert substitutes
    assert substitutes[0]["target_skill"] == "pytorch"
