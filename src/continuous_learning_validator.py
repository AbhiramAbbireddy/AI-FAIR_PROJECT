"""
Continuous learning validator for FAIR-PATH.

This module closes the loop after recommendations by:
- turning roadmap milestones into concrete checkpoints
- generating lightweight assessments per skill
- evaluating user answers and practical evidence
"""
from __future__ import annotations

from typing import Any

from src.models.schemas import (
    ContinuousLearningReport,
    LearningAssessmentQuestion,
    LearningAssessmentResult,
    LearningCheckpoint,
)


_SKILL_QUESTION_BANK: dict[str, list[dict[str, Any]]] = {
    "docker": [
        {
            "prompt": "Explain the difference between a Docker image and a Docker container.",
            "expected_points": ["immutable image template", "container is a running instance", "containers share host kernel"],
            "question_type": "short_answer",
        },
        {
            "prompt": "A container loses data after restart. How would you fix that?",
            "expected_points": ["use volumes", "bind mount or named volume", "persist state outside container"],
            "question_type": "scenario",
        },
    ],
    "aws": [
        {
            "prompt": "What is the difference between EC2 and S3, and when would you use each?",
            "expected_points": ["compute vs storage", "ec2 runs servers", "s3 stores objects/files"],
            "question_type": "short_answer",
        },
        {
            "prompt": "How would you deploy a simple API securely on AWS?",
            "expected_points": ["compute service", "network/security groups or IAM", "monitoring/logging"],
            "question_type": "scenario",
        },
    ],
    "pytorch": [
        {
            "prompt": "What are tensors and why are they central in PyTorch?",
            "expected_points": ["multidimensional arrays", "support gradients/autograd", "used for model inputs/weights"],
            "question_type": "short_answer",
        },
        {
            "prompt": "How would you structure a training loop in PyTorch?",
            "expected_points": ["forward pass", "loss calculation", "backpropagation", "optimizer step"],
            "question_type": "scenario",
        },
    ],
    "rag": [
        {
            "prompt": "What problem does RAG solve in LLM applications?",
            "expected_points": ["reduces hallucinations", "retrieves external context", "grounds answers in documents"],
            "question_type": "short_answer",
        },
        {
            "prompt": "How would you improve a weak RAG pipeline that returns irrelevant chunks?",
            "expected_points": ["better chunking", "improve retrieval/reranking", "metadata filters or prompt refinement"],
            "question_type": "scenario",
        },
    ],
    "langchain": [
        {
            "prompt": "What role does LangChain play in an LLM application stack?",
            "expected_points": ["orchestration", "chains/agents/tools", "retrieval or memory integration"],
            "question_type": "short_answer",
        },
        {
            "prompt": "How would you build a simple document Q&A app with LangChain?",
            "expected_points": ["load documents", "embed or index/retrieve", "prompt llm with context"],
            "question_type": "scenario",
        },
    ],
}


def _default_questions(skill: str) -> list[dict[str, Any]]:
    skill_name = skill.title()
    return [
        {
            "prompt": f"Explain the core concepts behind {skill_name} and how you would use it in a real project.",
            "expected_points": [f"{skill} fundamentals", "use case", "project context"],
            "question_type": "short_answer",
        },
        {
            "prompt": f"Describe one practical task or project where you would apply {skill_name}.",
            "expected_points": ["implementation steps", "practical example", "tradeoffs or validation"],
            "question_type": "scenario",
        },
    ]


def _practice_evidence(skill: str) -> list[str]:
    skill_name = skill.title()
    return [
        f"Build or publish one project that clearly demonstrates {skill_name}.",
        f"Document the setup, design choices, and tradeoffs for your {skill_name} work.",
        f"Prepare one interview-style explanation of how you used {skill_name} end to end.",
    ]


def _assessment_focus(skill: str) -> list[str]:
    return [
        f"{skill.title()} fundamentals",
        f"{skill.title()} practical usage",
        f"{skill.title()} debugging and tradeoffs",
    ]


def _extract_milestones(learning_path: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not learning_path:
        return []
    if "learning_path" in learning_path and isinstance(learning_path["learning_path"], dict):
        return list(learning_path["learning_path"].get("milestones", []))
    return list(learning_path.get("milestones", []))


def build_learning_validation_report(
    *,
    target_role: str,
    learning_path: dict[str, Any] | None,
    ranked_priorities: list[dict[str, Any]] | None = None,
) -> ContinuousLearningReport:
    milestones = _extract_milestones(learning_path)
    ranked_priorities = ranked_priorities or []

    checkpoints: list[LearningCheckpoint] = []
    seen: set[str] = set()
    priority_lookup = {
        str(item.get("skill", "")).strip().lower(): float(item.get("priority_score", 70.0))
        for item in ranked_priorities
        if str(item.get("skill", "")).strip()
    }

    for index, milestone in enumerate(milestones[:6], 1):
        skill = str(milestone.get("skill", "")).strip().lower()
        if not skill or skill in seen:
            continue
        seen.add(skill)
        questions_data = _SKILL_QUESTION_BANK.get(skill, _default_questions(skill))
        questions = [
            LearningAssessmentQuestion(
                skill=skill,
                difficulty="intermediate" if index <= 2 else "advanced",
                prompt=item["prompt"],
                expected_points=list(item.get("expected_points", [])),
                question_type=str(item.get("question_type", "short_answer")),
            )
            for item in questions_data
        ]
        month_start = milestone.get("month_start", milestone.get("month", index))
        month_end = milestone.get("month_end", month_start)
        duration_weeks = int(milestone.get("duration_weeks", max(4, (int(month_end) - int(month_start) + 1) * 4)))
        estimated_hours = duration_weeks * 3
        target_score = min(90.0, max(65.0, priority_lookup.get(skill, float(milestone.get("priority_score", 70.0))) * 0.9))
        label = f"Month {month_start}" if month_start == month_end else f"Months {month_start}-{month_end}"

        checkpoints.append(
            LearningCheckpoint(
                skill=skill,
                milestone_label=label,
                target_weeks=duration_weeks,
                target_score=round(target_score, 1),
                estimated_hours=estimated_hours,
                assessment_focus=_assessment_focus(skill),
                practice_evidence=_practice_evidence(skill),
                questions=questions,
            )
        )

    if not checkpoints:
        for index, item in enumerate(ranked_priorities[:4], 1):
            skill = str(item.get("skill", "")).strip().lower()
            if not skill or skill in seen:
                continue
            seen.add(skill)
            questions_data = _SKILL_QUESTION_BANK.get(skill, _default_questions(skill))
            checkpoints.append(
                LearningCheckpoint(
                    skill=skill,
                    milestone_label=f"Phase {index}",
                    target_weeks=4,
                    target_score=70.0,
                    estimated_hours=12,
                    assessment_focus=_assessment_focus(skill),
                    practice_evidence=_practice_evidence(skill),
                    questions=[
                        LearningAssessmentQuestion(
                            skill=skill,
                            difficulty="intermediate",
                            prompt=q["prompt"],
                            expected_points=list(q.get("expected_points", [])),
                            question_type=str(q.get("question_type", "short_answer")),
                        )
                        for q in questions_data
                    ],
                )
            )

    focus_skills = [checkpoint.skill for checkpoint in checkpoints[:5]]
    recommendations = [
        "After finishing each roadmap milestone, take a short checkpoint before moving to the next skill.",
        "Treat practice-project evidence as mandatory, not optional, for high-priority skills.",
        "If a skill scores below the checkpoint target, extend the milestone and repeat project work before continuing.",
    ]
    summary = (
        f"The validator created {len(checkpoints)} checkpoints for {target_role}. "
        f"Use them to confirm whether each roadmap skill is actually interview-ready."
    )
    return ContinuousLearningReport(
        target_role=target_role,
        summary=summary,
        checkpoints=checkpoints,
        focus_skills=focus_skills,
        recommendations=recommendations,
        source_status="rule_based",
    )


def evaluate_learning_checkpoint(
    checkpoint: LearningCheckpoint,
    answers: list[str],
    evidence_text: str = "",
) -> LearningAssessmentResult:
    theory_hits = 0
    theory_total = 0
    strengths: list[str] = []
    missing_points: list[str] = []

    for question, answer in zip(checkpoint.questions, answers):
        answer_lower = answer.lower()
        matched_for_question = 0
        for point in question.expected_points:
            theory_total += 1
            point_terms = [term.strip().lower() for term in point.replace("/", " ").split() if len(term.strip()) >= 3]
            if point_terms and any(term in answer_lower for term in point_terms):
                theory_hits += 1
                matched_for_question += 1
            else:
                missing_points.append(f"{checkpoint.skill.title()}: {point}")
        if matched_for_question:
            strengths.append(f"Covered {matched_for_question} expected ideas for one {checkpoint.skill.title()} checkpoint.")

    theory_score = round((theory_hits / max(theory_total, 1)) * 100.0, 1)

    evidence_lower = evidence_text.lower()
    practical_hits = 0
    for cue in checkpoint.practice_evidence:
        cue_terms = [term for term in cue.lower().replace("-", " ").split() if len(term) >= 4]
        if cue_terms and any(term in evidence_lower for term in cue_terms):
            practical_hits += 1
    practical_score = round((practical_hits / max(len(checkpoint.practice_evidence), 1)) * 100.0, 1)
    overall = round(theory_score * 0.7 + practical_score * 0.3, 1)

    if overall >= checkpoint.target_score + 10:
        readiness_level = "Ready"
        checkpoint_status = "ready"
    elif overall >= checkpoint.target_score:
        readiness_level = "On Track"
        checkpoint_status = "on_track"
    else:
        readiness_level = "Needs Reinforcement"
        checkpoint_status = "behind"

    next_actions: list[str] = []
    if theory_score < checkpoint.target_score:
        next_actions.append(f"Review {checkpoint.skill.title()} fundamentals and retry the checkpoint questions.")
    if practical_score < 50:
        next_actions.append(f"Build one concrete {checkpoint.skill.title()} project and document it before marking this milestone complete.")
    if not next_actions:
        next_actions.append(f"Move to the next roadmap milestone and keep one short revision session for {checkpoint.skill.title()} this week.")

    feedback = (
        f"Your {checkpoint.skill.title()} checkpoint scored {overall:.1f}% against a target of {checkpoint.target_score:.1f}%. "
        f"Theory understanding is {theory_score:.1f}% and practical evidence is {practical_score:.1f}%."
    )

    return LearningAssessmentResult(
        skill=checkpoint.skill,
        theory_score=theory_score,
        practical_score=practical_score,
        overall_score=overall,
        readiness_level=readiness_level,
        checkpoint_status=checkpoint_status,
        feedback=feedback,
        strengths=strengths[:4],
        missing_points=missing_points[:8],
        next_actions=next_actions,
    )
