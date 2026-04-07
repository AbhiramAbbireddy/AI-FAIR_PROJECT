"""
Portfolio impact analyzer for FAIR-PATH.

This component validates resume skill claims against a GitHub portfolio and
produces a practical portfolio score plus skill-level evidence.
"""
from __future__ import annotations

import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from src.models.schemas import ExtractedSkill, PortfolioReport, PortfolioRepository, PortfolioSkillEvidence
from src.skill_extraction.normalizer import normalize_skill


GITHUB_PROFILE_PATTERN = re.compile(
    r"github\.com/(?P<username>[A-Za-z0-9](?:[A-Za-z0-9-]{0,38}[A-Za-z0-9])?)(?:/)?",
    re.IGNORECASE,
)


def extract_github_username(text: str) -> str | None:
    match = GITHUB_PROFILE_PATTERN.search(text or "")
    if not match:
        return None
    username = match.group("username")
    reserved = {"features", "topics", "orgs", "about", "pricing", "contact"}
    return username if username and username.lower() not in reserved else None


def _github_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "fair-path-portfolio-analyzer",
    }
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _fetch_json(url: str) -> Any:
    request = Request(url, headers=_github_headers())
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _fetch_repositories(username: str, max_repos: int = 12) -> tuple[list[PortfolioRepository], str]:
    try:
        repos_payload = _fetch_json(f"https://api.github.com/users/{quote(username)}/repos?per_page={max_repos}&sort=updated")
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return [], "api_unavailable"

    repositories: list[PortfolioRepository] = []
    for repo in repos_payload:
        if repo.get("fork"):
            continue

        languages: list[str] = []
        languages_url = repo.get("languages_url")
        if languages_url:
            try:
                lang_payload = _fetch_json(languages_url)
                languages = list(lang_payload.keys())
            except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
                languages = [repo.get("language")] if repo.get("language") else []
        elif repo.get("language"):
            languages = [repo.get("language")]

        repositories.append(
            PortfolioRepository(
                name=str(repo.get("name", "")),
                url=str(repo.get("html_url", "")),
                description=str(repo.get("description") or ""),
                primary_language=str(repo.get("language") or ""),
                languages=[lang for lang in languages if lang],
                stars=int(repo.get("stargazers_count", 0) or 0),
                forks=int(repo.get("forks_count", 0) or 0),
                size_kb=int(repo.get("size", 0) or 0),
                pushed_at=repo.get("pushed_at"),
                topics=[str(topic) for topic in repo.get("topics", [])],
            )
        )

    return repositories, "api_live"


def _normalize_repo_tokens(repository: PortfolioRepository) -> set[str]:
    tokens: set[str] = set()
    raw_values = [repository.name, repository.description, repository.primary_language, *repository.languages, *repository.topics]
    for value in raw_values:
        if not value:
            continue
        text = re.sub(r"[^a-zA-Z0-9+#.\- ]", " ", str(value).lower())
        for token in text.split():
            if len(token) < 2:
                continue
            tokens.add(normalize_skill(token))
        normalized_phrase = normalize_skill(str(value))
        if normalized_phrase:
            tokens.add(normalized_phrase)
    return tokens


def _portfolio_skill_evidence(skills: list[ExtractedSkill], repositories: list[PortfolioRepository]) -> tuple[list[PortfolioSkillEvidence], list[PortfolioSkillEvidence]]:
    repo_token_sets = [_normalize_repo_tokens(repo) for repo in repositories]
    verified: list[PortfolioSkillEvidence] = []
    weak: list[PortfolioSkillEvidence] = []

    for skill in skills:
        canonical = normalize_skill(skill.canonical)
        matched_repos = [repo for repo, tokens in zip(repositories, repo_token_sets) if canonical in tokens]
        if matched_repos:
            confidence = min(1.0, 0.45 + len(matched_repos) * 0.18)
            evidence = [f"{repo.name} ({repo.primary_language or 'repo'})" for repo in matched_repos[:3]]
            status = "verified" if len(matched_repos) >= 2 or skill.proficiency_score >= 0.85 else "partial"
            payload = PortfolioSkillEvidence(
                skill=skill.canonical,
                status=status,
                confidence=round(confidence, 2),
                evidence=evidence,
            )
            if status == "verified":
                verified.append(payload)
            else:
                weak.append(payload)
        elif skill.proficiency_score >= 0.8:
            weak.append(
                PortfolioSkillEvidence(
                    skill=skill.canonical,
                    status="unverified",
                    confidence=0.2,
                    evidence=["Strong resume claim but no supporting repository signal found"],
                )
            )

    verified.sort(key=lambda item: (-item.confidence, item.skill))
    weak.sort(key=lambda item: (item.status != "unverified", -item.confidence, item.skill))
    return verified, weak


def _score_portfolio(repositories: list[PortfolioRepository]) -> tuple[float, float, float, float, float]:
    if not repositories:
        return 0.0, 0.0, 0.0, 0.0, 0.0

    now = datetime.now(timezone.utc)
    total_repos = len(repositories)
    total_stars = sum(repo.stars for repo in repositories)
    total_forks = sum(repo.forks for repo in repositories)
    language_count = len({lang.lower() for repo in repositories for lang in repo.languages if lang})
    documented = sum(1 for repo in repositories if repo.description.strip())
    active_recent = 0
    for repo in repositories:
        if not repo.pushed_at:
            continue
        try:
            pushed_at = datetime.fromisoformat(repo.pushed_at.replace("Z", "+00:00"))
        except ValueError:
            continue
        if (now - pushed_at).days <= 180:
            active_recent += 1

    activity_score = min(25.0, total_repos * 1.2 + active_recent * 2.0)
    complexity_score = min(25.0, language_count * 3.0 + sum(min(repo.size_kb / 250.0, 4.0) for repo in repositories))
    documentation_score = min(20.0, documented * 2.0)
    impact_score = min(30.0, total_stars * 1.5 + total_forks * 2.0)
    total_score = round(activity_score + complexity_score + documentation_score + impact_score, 1)
    return total_score, round(activity_score, 1), round(complexity_score, 1), round(documentation_score, 1), round(impact_score, 1)


def _recommendations(
    report: PortfolioReport,
    skills: list[ExtractedSkill],
) -> list[str]:
    recommendations: list[str] = []
    if not report.github_username:
        recommendations.append("Add a GitHub profile link to the resume so portfolio validation can verify project-based skills.")
        return recommendations

    if not report.repositories:
        recommendations.append("Create or publish at least 2 public repositories that demonstrate your strongest target-role skills.")
        return recommendations

    if report.documentation_score < 10:
        recommendations.append("Improve repository descriptions and README quality to strengthen documentation credibility.")
    if report.activity_score < 12:
        recommendations.append("Show more recent activity with consistent commits or updated projects in the last 6 months.")
    if report.impact_score < 6:
        recommendations.append("Add polished showcase projects with clear outcomes, usage steps, and visible problem statements.")
    if report.weak_skills:
        missing = ", ".join(item.skill for item in report.weak_skills[:3])
        recommendations.append(f"Build or expose portfolio evidence for these resume claims: {missing}.")
    high_value_skills = [skill.canonical for skill in skills if skill.proficiency_score >= 0.8][:3]
    if high_value_skills:
        recommendations.append(f"Pin repositories that best prove your strongest skills: {', '.join(high_value_skills)}.")
    return recommendations[:4]


def analyze_portfolio(
    *,
    resume_text: str,
    extracted_skills: list[ExtractedSkill],
    github_profile: str | None = None,
) -> PortfolioReport:
    username = extract_github_username(github_profile or "") or extract_github_username(resume_text)
    profile_url = f"https://github.com/{username}" if username else None

    repositories: list[PortfolioRepository] = []
    source_status = "resume_only"
    if username:
        repositories, source_status = _fetch_repositories(username)

    verified_skills, weak_skills = _portfolio_skill_evidence(extracted_skills, repositories)
    portfolio_score, activity_score, complexity_score, documentation_score, impact_score = _score_portfolio(repositories)

    report = PortfolioReport(
        github_username=username,
        profile_url=profile_url,
        portfolio_score=portfolio_score,
        activity_score=activity_score,
        complexity_score=complexity_score,
        documentation_score=documentation_score,
        impact_score=impact_score,
        verified_skills=verified_skills,
        weak_skills=weak_skills,
        repositories=repositories[:8],
        source_status=source_status if username else "not_checked",
    )

    report.recommendations = _recommendations(report, extracted_skills)
    repo_count = len(report.repositories)
    verified_count = len([item for item in report.verified_skills if item.status == "verified"])
    if username and source_status == "api_live":
        report.summary = (
            f"Analyzed {repo_count} repositories for @{username}. "
            f"Verified {verified_count} skill claims with a portfolio score of {report.portfolio_score:.1f}/100."
        )
    elif username:
        report.summary = (
            f"Detected GitHub profile @{username}, but live repository analysis is unavailable right now. "
            "Resume-linked portfolio validation is ready once GitHub API access succeeds."
        )
    else:
        report.summary = "No GitHub profile detected yet. Add a GitHub URL to validate resume skills against real projects."
    return report
