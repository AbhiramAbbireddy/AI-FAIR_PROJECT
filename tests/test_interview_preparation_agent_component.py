from src.interview_preparation_agent import evaluate_mock_answer, generate_interview_prep


def test_generate_interview_prep_returns_questions():
    report = generate_interview_prep(
        target_role="LLM Engineer",
        match_score=62.0,
        missing_skills=["docker", "langchain", "retrieval-augmented generation"],
        weak_skills=["python"],
        portfolio_score=48.0,
    )

    assert report.target_role == "LLM Engineer"
    assert report.questions
    assert report.focus_skills
    assert report.success_probability > 0


def test_evaluate_mock_answer_flags_missing_points():
    report = generate_interview_prep(
        target_role="Backend Developer",
        match_score=70.0,
        missing_skills=["docker"],
        weak_skills=[],
        portfolio_score=55.0,
    )
    question = report.questions[0]
    evaluation = evaluate_mock_answer(question, "Docker helps package applications.")

    assert evaluation.overall >= 0
    assert evaluation.feedback
    assert isinstance(evaluation.missing_points, list)
