from src.models.schemas import ExtractedSkill
from src.portfolio_analyzer import analyze_portfolio, extract_github_username


def test_extract_github_username_from_resume_text():
    text = "GitHub: https://github.com/example-user and projects built with Python"
    assert extract_github_username(text) == "example-user"


def test_portfolio_analyzer_without_github_profile():
    report = analyze_portfolio(
        resume_text="Built Python and FastAPI projects.",
        extracted_skills=[
            ExtractedSkill(
                name="Python",
                canonical="python",
                proficiency="advanced",
                proficiency_score=0.88,
            ),
            ExtractedSkill(
                name="FastAPI",
                canonical="fastapi",
                proficiency="intermediate",
                proficiency_score=0.70,
            ),
        ],
    )

    assert report.github_username is None
    assert report.source_status == "not_checked"
    assert report.portfolio_score == 0.0
    assert report.recommendations
