from src.fairness_evaluator import anonymize_resume_text, evaluate_fairness


def test_evaluate_fairness_detects_gender_and_age_signals():
    text = """
    Mr. Rahul Sharma
    Date of Birth: 12-03-1998
    Male
    Married
    """

    report = evaluate_fairness(text)

    assert report.score < 100
    assert report.gender_bias != "None detected"
    assert report.age_bias != "None detected"
    assert report.mitigated_score >= report.score


def test_anonymize_resume_text_removes_demographic_details():
    anonymized = anonymize_resume_text(
        "Mr. John Smith john@example.com +91 9876543210 Date of Birth: 10/10/1990"
    )

    assert "john@example.com" not in anonymized.lower()
    assert "date of birth" not in anonymized.lower()
    assert "[email removed]" in anonymized
