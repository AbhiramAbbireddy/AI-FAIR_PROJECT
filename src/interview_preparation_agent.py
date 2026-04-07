"""
Interview preparation agent for FAIR-PATH.

Generates targeted interview questions from role gaps and portfolio evidence,
then evaluates practice answers with a lightweight rubric.
"""
from __future__ import annotations

from typing import Any

from src.models.schemas import (
    InterviewAnswerEvaluation,
    InterviewPrepReport,
    InterviewQuestion,
)
from src.skill_extraction.normalizer import normalize_skill


_QUESTION_TEMPLATES: dict[str, dict[str, tuple[str, list[str]]]] = {
    "docker": {
        "technical": (
            "Explain the difference between Docker containers and virtual machines.",
            ["lightweight isolation", "shared host kernel", "faster startup", "packaging dependencies"],
        ),
        "practical": (
            "How would you containerize a Python or FastAPI application using Docker?",
            ["Dockerfile", "base image", "install dependencies", "expose port", "run command"],
        ),
        "scenario": (
            "A Dockerized service works locally but fails in production. How would you debug it?",
            ["logs", "environment variables", "networking", "image mismatch", "resource limits"],
        ),
        "behavioral": (
            "Tell me about a time you used containers to simplify development or deployment.",
            ["problem", "your action", "tooling choice", "outcome"],
        ),
    },
    "langchain": {
        "technical": (
            "What problem does LangChain solve in LLM application development?",
            ["chains", "prompt orchestration", "retrieval", "tool calling", "memory"],
        ),
        "practical": (
            "How would you build a retrieval-augmented application with LangChain?",
            ["document loading", "chunking", "retriever", "prompt", "llm response"],
        ),
        "scenario": (
            "Your LangChain pipeline is hallucinating. What would you improve first?",
            ["retrieval quality", "prompt grounding", "context size", "citations", "evaluation"],
        ),
        "behavioral": (
            "Describe an LLM workflow you built and how you improved reliability.",
            ["project context", "changes made", "measurement", "result"],
        ),
    },
    "retrieval-augmented generation": {
        "technical": (
            "What is retrieval-augmented generation and why is it useful?",
            ["retrieval", "grounded context", "reduced hallucination", "external knowledge"],
        ),
        "practical": (
            "Walk through the main components of a RAG pipeline.",
            ["chunking", "embedding or retrieval", "index", "retriever", "generation"],
        ),
        "scenario": (
            "Your RAG answers are irrelevant for some queries. How would you troubleshoot?",
            ["query reformulation", "chunk size", "ranking", "metadata filters", "evaluation"],
        ),
        "behavioral": (
            "Tell me about a project where retrieval improved an AI system.",
            ["problem", "retrieval design", "outcome", "lesson learned"],
        ),
    },
}


def _default_templates(skill: str) -> dict[str, tuple[str, list[str]]]:
    skill_name = skill.title()
    return {
        "technical": (
            f"What are the core concepts of {skill_name}?",
            ["definition", "core components", "when to use it"],
        ),
        "practical": (
            f"How would you use {skill_name} in a real project for this role?",
            ["implementation steps", "tooling", "example use case"],
        ),
        "scenario": (
            f"You are given a project that depends on {skill_name}. How would you approach delivery?",
            ["requirements", "design choices", "testing", "tradeoffs"],
        ),
        "behavioral": (
            f"Describe a time you used {skill_name} or a related tool to solve a difficult problem.",
            ["context", "action", "result"],
        ),
    }


def _difficulty_for_role(role_name: str) -> str:
    role = role_name.lower()
    if any(token in role for token in ["senior", "lead", "architect", "staff"]):
        return "senior"
    if any(token in role for token in ["intern", "junior", "entry"]):
        return "junior"
    return "mid"


def _question_bank_for_skill(skill: str, difficulty: str) -> list[InterviewQuestion]:
    normalized = normalize_skill(skill)
    templates = _QUESTION_TEMPLATES.get(normalized, _default_templates(skill))
    return [
        InterviewQuestion(
            skill=normalized,
            category=category,
            difficulty=difficulty,
            question=question,
            expected_points=expected_points,
        )
        for category, (question, expected_points) in templates.items()
    ]


def _success_probability(
    *,
    match_score: float,
    portfolio_score: float,
    missing_skill_count: int,
    weak_skill_count: int,
) -> float:
    probability = 0.35
    probability += min(match_score, 100.0) * 0.0035
    probability += min(portfolio_score, 100.0) * 0.0020
    probability -= min(missing_skill_count, 8) * 0.04
    probability -= min(weak_skill_count, 5) * 0.03
    return round(max(0.10, min(0.95, probability)) * 100.0, 1)


def generate_interview_prep(
    *,
    target_role: str,
    match_score: float,
    missing_skills: list[str],
    weak_skills: list[str] | None = None,
    portfolio_score: float = 0.0,
) -> InterviewPrepReport:
    weak_skills = weak_skills or []
    difficulty = _difficulty_for_role(target_role)

    focus_skills = []
    seen: set[str] = set()
    for skill in [*missing_skills, *weak_skills]:
        normalized = normalize_skill(skill)
        if normalized and normalized not in seen:
            seen.add(normalized)
            focus_skills.append(normalized)
    focus_skills = focus_skills[:5]

    questions: list[InterviewQuestion] = []
    for skill in focus_skills:
        questions.extend(_question_bank_for_skill(skill, difficulty))

    probability = _success_probability(
        match_score=match_score,
        portfolio_score=portfolio_score,
        missing_skill_count=len(missing_skills),
        weak_skill_count=len(weak_skills),
    )

    if probability >= 80:
        readiness = "Strong"
    elif probability >= 60:
        readiness = "Developing"
    else:
        readiness = "Needs focused preparation"

    recommendations = []
    if focus_skills:
        recommendations.append(f"Practice these highest-risk interview areas first: {', '.join(focus_skills[:3])}.")
    if weak_skills:
        recommendations.append("Strengthen examples from real projects so your answers include proof, not only theory.")
    if match_score < 70:
        recommendations.append("Rehearse how your current experience maps to the target role before going deep on technical answers.")
    if portfolio_score < 40:
        recommendations.append("Prepare 2 strong project stories using problem, implementation, tradeoff, and result format.")

    summary = (
        f"Interview preparation is focused on {len(focus_skills)} high-priority skill areas for {target_role}. "
        f"Estimated success probability is {probability:.1f}%."
    )

    return InterviewPrepReport(
        target_role=target_role,
        success_probability=probability,
        readiness_level=readiness,
        focus_skills=focus_skills,
        questions=questions,
        recommendations=recommendations[:4],
        summary=summary,
        source_status="rule_based",
    )


def evaluate_mock_answer(question: InterviewQuestion, answer: str) -> InterviewAnswerEvaluation:
    normalized_answer = (answer or "").strip().lower()
    if not normalized_answer:
        return InterviewAnswerEvaluation(
            feedback="Answer is empty. Start with a short definition, then explain your approach with one concrete example.",
            missing_points=list(question.expected_points),
        )

    matched_points = []
    missing_points = []
    for point in question.expected_points:
        point_tokens = [token for token in normalize_skill(point).split() if token]
        if point_tokens and any(token in normalized_answer for token in point_tokens):
            matched_points.append(point)
        else:
            missing_points.append(point)

    correctness = round(min(100.0, 35.0 + len(matched_points) * 15.0), 1)
    completeness = round((len(matched_points) / max(len(question.expected_points), 1)) * 100.0, 1)
    clarity = 85.0 if len(answer.split()) >= 40 else 70.0 if len(answer.split()) >= 20 else 55.0
    overall = round(correctness * 0.4 + completeness * 0.4 + clarity * 0.2, 1)

    if overall >= 80:
        feedback = "Strong answer. Keep the structure and add one short real-world example for even more credibility."
    elif overall >= 60:
        feedback = "Decent answer, but it needs more coverage of the missing technical points and a clearer example."
    else:
        feedback = "This answer is still weak. Start with the core definition, then explain the practical steps and tradeoffs."

    return InterviewAnswerEvaluation(
        correctness=correctness,
        completeness=completeness,
        clarity=clarity,
        overall=overall,
        feedback=feedback,
        missing_points=missing_points,
    )
