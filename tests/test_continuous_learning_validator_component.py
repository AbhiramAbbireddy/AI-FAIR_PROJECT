from src.continuous_learning_validator import (
    build_learning_validation_report,
    evaluate_learning_checkpoint,
)


def test_build_learning_validation_report_from_milestones():
    learning_path = {
        "milestones": [
            {
                "skill": "docker",
                "month_start": 1,
                "month_end": 1,
                "duration_weeks": 4,
                "priority_score": 88,
            },
            {
                "skill": "aws",
                "month_start": 2,
                "month_end": 3,
                "duration_weeks": 6,
                "priority_score": 82,
            },
        ]
    }

    report = build_learning_validation_report(
        target_role="Machine Learning Engineer",
        learning_path=learning_path,
        ranked_priorities=[
            {"skill": "docker", "priority_score": 88},
            {"skill": "aws", "priority_score": 82},
        ],
    )

    assert report.target_role == "Machine Learning Engineer"
    assert len(report.checkpoints) >= 2
    assert report.checkpoints[0].skill == "docker"


def test_evaluate_learning_checkpoint_scores_expected_points():
    report = build_learning_validation_report(
        target_role="Machine Learning Engineer",
        learning_path={"milestones": [{"skill": "docker", "month_start": 1, "month_end": 1, "duration_weeks": 4}]},
        ranked_priorities=[{"skill": "docker", "priority_score": 90}],
    )
    checkpoint = report.checkpoints[0]

    result = evaluate_learning_checkpoint(
        checkpoint,
        answers=[
            "A docker image is an immutable template and a container is a running instance that shares the host kernel.",
            "I would use a named volume or bind mount so the data persists outside the container.",
        ],
        evidence_text="I built a Docker project, documented the setup, and prepared an interview explanation.",
    )

    assert result.skill == "docker"
    assert result.theory_score > 50
    assert result.practical_score > 0
    assert result.overall_score > 0
