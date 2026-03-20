"""
Canonical priority ranking component for FAIR-PATH.

Ranks missing skills using the weighted framework from the project design:
- Job Importance: 40%
- Market Demand: 30%
- Learning Ease: 20%
- Salary Impact: 10%
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.config.settings import BASE_DIR


@dataclass(slots=True)
class PriorityRankerConfig:
    job_importance_weight: float = 0.40
    market_demand_weight: float = 0.30
    learning_ease_weight: float = 0.20
    salary_impact_weight: float = 0.10
    learning_db_path: Path = BASE_DIR / "data" / "learning_time_database.json"
    salary_db_path: Path = BASE_DIR / "data" / "salary_impact_database.json"


class PriorityRanker:
    """Ranks missing skills by practical learning priority."""

    def __init__(
        self,
        trend_data: dict[str, dict[str, Any]] | list[dict[str, Any]] | None = None,
        config: PriorityRankerConfig | None = None,
    ):
        self.config = config or PriorityRankerConfig()
        self.learning_time_db = self._load_json(self.config.learning_db_path)
        self.salary_db = self._load_json(self.config.salary_db_path)
        self.trend_data = self._normalize_trend_data(trend_data)

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _normalize_skill(skill: str) -> str:
        return skill.strip().lower()

    def _normalize_trend_data(
        self,
        trend_data: dict[str, dict[str, Any]] | list[dict[str, Any]] | None,
    ) -> dict[str, dict[str, Any]]:
        if not trend_data:
            return {}

        normalized: dict[str, dict[str, Any]] = {}
        if isinstance(trend_data, dict):
            for skill, payload in trend_data.items():
                normalized[self._normalize_skill(skill)] = {
                    "growth_rate": float(payload.get("growth_rate", payload.get("growth_pct", 0.0))),
                    "trend": str(payload.get("trend", payload.get("forecast_demand", "Unknown"))),
                    "current_pct": float(payload.get("current_pct", 0.0)),
                }
            return normalized

        for item in trend_data:
            skill = str(item.get("skill", "")).strip()
            if not skill:
                continue
            normalized[self._normalize_skill(skill)] = {
                "growth_rate": float(item.get("growth_rate", item.get("growth_pct", 0.0))),
                "trend": str(item.get("trend", item.get("forecast_demand", "Unknown"))),
                "current_pct": float(item.get("current_pct", 0.0)),
            }
        return normalized

    def update_trend_data(self, trend_data: dict[str, dict[str, Any]] | list[dict[str, Any]] | None) -> None:
        self.trend_data = self._normalize_trend_data(trend_data)

    def calculate_job_importance(
        self,
        skill: str,
        job_description: str,
        category: str,
        mention_count: int | None = None,
    ) -> float:
        normalized_category = category.upper()
        base_scores = {
            "CRITICAL": 95.0,
            "IMPORTANT": 75.0,
            "NICE_TO_HAVE": 40.0,
        }
        base_score = base_scores.get(normalized_category, 55.0)
        mentions = mention_count if mention_count is not None else self.count_skill_mentions(skill, job_description)
        mention_bonus = min(mentions * 5.0, 20.0)

        text = job_description.lower()
        skill_lower = self._normalize_skill(skill)
        keyword_bonus = 0.0
        if skill_lower in text:
            keyword_bonus += 5.0
        if any(token in text for token in ["required", "must have", "essential", "mandatory"]) and skill_lower in text:
            keyword_bonus += 5.0

        return round(min(base_score + mention_bonus + keyword_bonus, 100.0), 2)

    def calculate_market_demand(self, skill: str) -> float:
        payload = self.trend_data.get(self._normalize_skill(skill))
        if payload:
            growth = float(payload.get("growth_rate", 0.0))
            current_pct = float(payload.get("current_pct", 0.0))
            if growth >= 30:
                return 95.0
            if growth >= 15:
                return 85.0
            if growth >= 5:
                return 70.0
            if growth >= -5:
                return 55.0 + min(current_pct, 20.0) * 0.5
            return 25.0

        salary_payload = self.salary_db.get(self._normalize_skill(skill), {})
        demand_label = str(salary_payload.get("demand", "moderate")).lower()
        demand_map = {
            "very high": 90.0,
            "high": 75.0,
            "moderate": 55.0,
            "low": 30.0,
        }
        return demand_map.get(demand_label, 50.0)

    def calculate_learning_ease(self, skill: str) -> float:
        payload = self.learning_time_db.get(self._normalize_skill(skill), {})
        months = float(payload.get("months_to_learn", 6))
        if months <= 2:
            return 95.0
        if months <= 4:
            return 80.0
        if months <= 6:
            return 60.0
        if months <= 12:
            return 40.0
        return 20.0

    def calculate_salary_impact(self, skill: str) -> float:
        payload = self.salary_db.get(self._normalize_skill(skill), {})
        salary_boost = float(payload.get("average_boost_inr", 250000))
        if salary_boost >= 500000:
            return 95.0
        if salary_boost >= 300000:
            return 80.0
        if salary_boost >= 200000:
            return 65.0
        return 40.0

    @staticmethod
    def count_skill_mentions(skill: str, job_description: str) -> int:
        if not skill or not job_description:
            return 0
        pattern = r"\b" + re.escape(skill) + r"\b"
        return len(re.findall(pattern, job_description, flags=re.IGNORECASE))

    def calculate_priority_score(
        self,
        skill: str,
        *,
        job_description: str = "",
        category: str = "IMPORTANT",
        mention_count: int | None = None,
    ) -> dict[str, Any]:
        scores = {
            "job_importance": self.calculate_job_importance(skill, job_description, category, mention_count),
            "market_demand": self.calculate_market_demand(skill),
            "learning_ease": self.calculate_learning_ease(skill),
            "salary_impact": self.calculate_salary_impact(skill),
        }

        priority_score = (
            scores["job_importance"] * self.config.job_importance_weight
            + scores["market_demand"] * self.config.market_demand_weight
            + scores["learning_ease"] * self.config.learning_ease_weight
            + scores["salary_impact"] * self.config.salary_impact_weight
        )

        normalized_skill = self._normalize_skill(skill)
        learning_time = self.learning_time_db.get(normalized_skill, {}).get("months_to_learn", "Unknown")
        salary_boost = self.salary_db.get(normalized_skill, {}).get("average_boost_inr", "N/A")

        return {
            "skill": normalized_skill,
            "priority_score": round(priority_score, 2),
            "rank_tier": self._rank_to_tier(priority_score),
            "breakdown": {key: round(float(value), 2) for key, value in scores.items()},
            "category": category.upper(),
            "learning_time_months": learning_time,
            "salary_boost_inr": salary_boost,
            "market_context": self.trend_data.get(normalized_skill, {}),
            "recommendation": self._generate_recommendation(priority_score, scores),
        }

    @staticmethod
    def _rank_to_tier(score: float) -> str:
        if score >= 85:
            return "CRITICAL"
        if score >= 70:
            return "HIGH"
        if score >= 50:
            return "MEDIUM"
        return "LOW"

    def _generate_recommendation(self, priority_score: float, scores: dict[str, float]) -> str:
        tier = self._rank_to_tier(priority_score)
        if tier == "CRITICAL":
            if scores["learning_ease"] >= 80:
                return "Learn this first. It is both high-impact and relatively quick to pick up."
            return "Start this early. It is strategically important even if it takes longer."
        if tier == "HIGH":
            if scores["market_demand"] >= 80:
                return "Strong market signal. Schedule this in the next learning cycle."
            return "Important for the target role. Plan this soon after the top priority skill."
        if tier == "MEDIUM":
            return "Useful supporting skill. Add it after the core blockers are covered."
        return "Lower urgency. Learn it later or only if your target role keeps requiring it."

    def rank_all_gaps(
        self,
        categorized_gaps: dict[str, list[str]],
        job_description: str = "",
    ) -> list[dict[str, Any]]:
        ranked: list[dict[str, Any]] = []
        for category, skills in categorized_gaps.items():
            for skill in skills:
                ranked.append(
                    self.calculate_priority_score(
                        skill,
                        job_description=job_description,
                        category=category.upper(),
                        mention_count=self.count_skill_mentions(skill, job_description),
                    )
                )
        ranked.sort(key=lambda item: item["priority_score"], reverse=True)
        return ranked

    def rank_missing_skills_for_job(
        self,
        *,
        missing_skills: list[str],
        job_description: str = "",
        required_skills: list[str] | None = None,
        optional_skills: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        required_set = {self._normalize_skill(skill) for skill in (required_skills or [])}
        optional_set = {self._normalize_skill(skill) for skill in (optional_skills or [])}

        categorized: dict[str, list[str]] = {
            "critical": [],
            "important": [],
            "nice_to_have": [],
        }
        for skill in missing_skills:
            normalized = self._normalize_skill(skill)
            if normalized in required_set:
                categorized["critical"].append(normalized)
            elif normalized in optional_set:
                categorized["nice_to_have"].append(normalized)
            else:
                categorized["important"].append(normalized)
        return self.rank_all_gaps(categorized, job_description)

    def get_ranking_summary(self, ranked_skills: list[dict[str, Any]]) -> str:
        lines = ["Priority Ranking Summary", "========================"]
        for index, skill_data in enumerate(ranked_skills[:5], 1):
            lines.append(
                f"{index}. {skill_data['skill']} - {skill_data['priority_score']}/100 "
                f"({skill_data['rank_tier']})"
            )
            lines.append(
                f"   Learn in: {skill_data['learning_time_months']} months | "
                f"Salary boost: ₹{skill_data['salary_boost_inr']}"
            )
            lines.append(f"   {skill_data['recommendation']}")
        return "\n".join(lines)
