<<<<<<< HEAD
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
=======
"""
Groq-powered learning path generator for FAIR-PATH.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

try:
    from groq import Groq

    HAS_GROQ = True
except ImportError:
    Groq = None
    HAS_GROQ = False


CACHE_DIR = Path("cache/learning_paths")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_key(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _load_cache(key: str) -> dict | None:
    path = CACHE_DIR / f"{key}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _save_cache(key: str, data: dict) -> None:
    path = CACHE_DIR / f"{key}.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _build_prompt(
    current_skills: list[str],
    missing_skills: list[str],
    priority_rankings: dict[str, float],
    match_score: float,
    target_role: str,
    hours_per_day: float = 2.0,
    learning_style: str = "hands-on",
    budget: str = "budget-friendly",
) -> str:
    ranked = sorted(
        missing_skills,
        key=lambda skill: priority_rankings.get(skill.lower(), priority_rankings.get(skill, 50.0)),
        reverse=True,
    )
    ranked_text = "\n".join(
        f"- {skill}: priority score {priority_rankings.get(skill.lower(), priority_rankings.get(skill, 50.0))}/100"
        for skill in ranked
    )

    current_skill_text = ", ".join(current_skills) if current_skills else "none yet"
    return f"""You are an expert career advisor specializing in tech learning paths.

USER PROFILE:
- Target role: {target_role}
- Current match score: {match_score:.0f}%
- Current skills: {current_skill_text}
- Missing skills (ranked by priority):
{ranked_text}
- Daily study time: {hours_per_day} hours/day
- Learning style: {learning_style}
- Budget: {budget}

TASK:
Create a realistic month-by-month roadmap to reach the target role and improve the match score toward 90% or higher.

RULES:
1. Respect skill prerequisites where relevant.
2. Higher priority skills should generally appear earlier.
3. Recommend specific resources and practical projects.
4. Keep the roadmap realistic for the available study time.
5. Respond with valid JSON only.

JSON SCHEMA:
{{
  "summary": "One sentence overview",
  "total_months": 6,
  "final_match_score": 90,
  "milestones": [
    {{
      "id": "m1",
      "month_start": 1,
      "month_end": 2,
      "skill": "Docker",
      "priority_score": 91.1,
      "duration_weeks": 6,
      "resources": [
        {{
          "name": "Docker for Beginners",
          "platform": "YouTube",
          "cost": "free",
          "url_hint": "search docker for beginners youtube"
        }}
      ],
      "practice_projects": [
        "Containerize a Flask app"
      ],
      "match_score_after": 80,
      "score_improvement": 5
    }}
  ]
}}"""


def _call_groq(prompt: str, api_key: str, retries: int = 3) -> str:
    if not HAS_GROQ or Groq is None:
        raise ImportError("groq package is not installed.")

    client = Groq(api_key=api_key) if api_key else Groq()
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=2000,
                temperature=0.3,
                top_p=1,
                stop=None,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            if attempt == retries - 1:
                raise RuntimeError(f"Groq API failed after {retries} attempts: {exc}") from exc
            time.sleep(2**attempt)
    raise RuntimeError("Groq API did not return a response.")


def _extract_json(raw: str) -> dict:
    raw = re.sub(r"```(?:json)?", "", raw).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError("No valid JSON found in Groq response.")


def _normalize_roadmap(result: dict, match_score: float) -> dict:
    milestones = result.get("milestones", [])
    normalized = {
        "summary": result.get("summary", "Personalized roadmap generated from your missing skills and priorities."),
        "total_months": int(result.get("total_months", len(milestones) or 1)),
        "final_match_score": int(result.get("final_match_score", min(95, int(match_score) + 15))),
        "milestones": [],
    }

    for index, milestone in enumerate(milestones, 1):
        normalized["milestones"].append(
            {
                "id": milestone.get("id", f"m{index}"),
                "month_start": int(milestone.get("month_start", index)),
                "month_end": int(milestone.get("month_end", milestone.get("month_start", index))),
                "skill": milestone.get("skill", f"Skill {index}"),
                "priority_score": float(milestone.get("priority_score", 70.0)),
                "duration_weeks": int(milestone.get("duration_weeks", 4)),
                "resources": milestone.get("resources", []),
                "practice_projects": milestone.get("practice_projects", []),
                "match_score_after": int(milestone.get("match_score_after", min(95, int(match_score) + index * 4))),
                "score_improvement": int(milestone.get("score_improvement", 4)),
            }
        )

    return normalized


def _fallback_learning_path(
    current_skills: list[str],
    missing_skills: list[str],
    priority_rankings: dict[str, float],
    match_score: float,
    target_role: str,
) -> dict:
    ranked = sorted(
        missing_skills,
        key=lambda skill: priority_rankings.get(skill.lower(), priority_rankings.get(skill, 50.0)),
        reverse=True,
    )
    milestones = []
    current_score = int(match_score)
    for index, skill in enumerate(ranked[:6], 1):
        improvement = max(2, min(8, int(priority_rankings.get(skill.lower(), priority_rankings.get(skill, 50.0)) // 15)))
        current_score = min(95, current_score + improvement)
        milestones.append(
            {
                "id": f"m{index}",
                "month_start": index,
                "month_end": index,
                "skill": skill,
                "priority_score": float(priority_rankings.get(skill.lower(), priority_rankings.get(skill, 50.0))),
                "duration_weeks": 4,
                "resources": [
                    {
                        "name": f"{skill.title()} Official Documentation",
                        "platform": "docs",
                        "cost": "free",
                        "url_hint": f"search {skill} official docs",
                    }
                ],
                "practice_projects": [f"Build a small project using {skill}"],
                "match_score_after": current_score,
                "score_improvement": improvement,
            }
        )

    return {
        "summary": f"Structured roadmap for reaching {target_role} using your highest-priority missing skills.",
        "total_months": len(milestones),
        "final_match_score": current_score,
        "milestones": milestones,
    }


def generate_learning_path(
    current_skills: list[str],
    missing_skills: list[str],
    priority_rankings: dict[str, float],
    match_score: float,
    target_role: str,
    hours_per_day: float = 2.0,
    learning_style: str = "hands-on",
    budget: str = "budget-friendly",
    use_cache: bool = True,
    api_key: str | None = None,
) -> dict:
    load_dotenv()
    api_key = api_key or os.getenv("GROQ_API_KEY")

    payload = {
        "current_skills": sorted(current_skills),
        "missing_skills": sorted(missing_skills),
        "priority_rankings": priority_rankings,
        "match_score": match_score,
        "target_role": target_role,
        "hours_per_day": hours_per_day,
        "learning_style": learning_style,
        "budget": budget,
    }
    key = _cache_key(payload)

    if use_cache:
        cached = _load_cache(key)
        if cached:
            cached["_from_cache"] = True
            return cached

    if not api_key or not HAS_GROQ:
        fallback = _fallback_learning_path(
            current_skills=current_skills,
            missing_skills=missing_skills,
            priority_rankings=priority_rankings,
            match_score=match_score,
            target_role=target_role,
        )
        fallback["_from_cache"] = False
        fallback["_provider"] = "fallback"
        _save_cache(key, fallback)
        return fallback

    prompt = _build_prompt(**payload)
    raw = _call_groq(prompt, api_key=api_key)
    result = _extract_json(raw)
    normalized = _normalize_roadmap(result, match_score)
    normalized["_from_cache"] = False
    normalized["_provider"] = "groq"
    _save_cache(key, normalized)
    return normalized


class LLMLearningPathGenerator:
    """Compatibility wrapper used by the skill-gap pipeline."""

    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("GROQ_API_KEY")
        self.available = bool(self.api_key and HAS_GROQ)

    def generate_learning_path(
        self,
        user_skills: list[str],
        missing_skills: list[dict[str, Any]],
        job_title: str,
        job_description: str,
        current_match_score: float,
        user_context: dict[str, Any] | None = None,
    ) -> dict:
        user_context = user_context or {}
        skill_names = [item.get("skill", "") for item in missing_skills if item.get("skill")]
        priority_rankings = {
            item.get("skill", "").lower(): float(item.get("priority_score", 50.0))
            for item in missing_skills
            if item.get("skill")
        }

        roadmap = generate_learning_path(
            current_skills=user_skills,
            missing_skills=skill_names,
            priority_rankings=priority_rankings,
            match_score=current_match_score,
            target_role=job_title,
            hours_per_day=float(user_context.get("hours_per_day", 2.0)),
            learning_style=str(user_context.get("learning_style", "hands-on")),
            budget=str(user_context.get("budget", "budget-friendly")),
            api_key=self.api_key,
        )

        return {
            "learning_path": roadmap,
            "provider": roadmap.get("_provider", "fallback"),
        }
>>>>>>> 762d549ff5cab1fc93bc6825be5008a3d4e0034c
