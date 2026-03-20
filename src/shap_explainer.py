"""
Canonical SHAP explainability component for FAIR-PATH.

This module explains why a resume matches a job posting or role by:
1. engineering interpretable features for resume-target pairs
2. training a local tree-based surrogate on the current resume against a
   background set of jobs or roles
3. applying SHAP TreeExplainer to the selected match

The fallback path still returns useful factor-level explanations when SHAP or
scikit-learn is unavailable.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from src.job_roles_database import get_job_role, load_job_roles
from src.matching.semantic_matcher import _experience_score
from src.models.schemas import JobPosting, MatchResult
from src.role_mapping.matcher import RoleMatch


@dataclass(slots=True)
class ExplainableTarget:
    target_id: str
    title: str
    description: str = ""
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    experience_level: str = "Not specified"
    target_type: str = "job"


@dataclass(slots=True)
class SHAPExplainerConfig:
    max_background_targets: int = 400
    max_skill_features: int = 18
    random_state: int = 42
    top_factors: int = 6


def build_role_targets() -> list[ExplainableTarget]:
    targets: list[ExplainableTarget] = []
    for role in load_job_roles():
        targets.append(
            ExplainableTarget(
                target_id=f"role::{role.role}",
                title=role.role,
                description=role.description,
                required_skills=list(role.core_skills),
                preferred_skills=list(role.optional_skills),
                experience_level="Not specified",
                target_type="role",
            )
        )
    return targets


def build_job_targets(postings: list[JobPosting]) -> list[ExplainableTarget]:
    return [
        ExplainableTarget(
            target_id=posting.job_id,
            title=posting.title,
            description=posting.description,
            required_skills=list(posting.required_skills),
            preferred_skills=list(posting.preferred_skills),
            experience_level=posting.experience_level,
            target_type="job",
        )
        for posting in postings
    ]


class MatchSHAPExplainer:
    def __init__(self, config: SHAPExplainerConfig | None = None):
        self.config = config or SHAPExplainerConfig()

    def explain_job_matches(
        self,
        resume_text: str,
        resume_skills: list[str],
        matches: list[MatchResult],
        postings: list[JobPosting],
    ) -> dict[str, dict[str, Any]]:
        if not matches:
            return {}

        background_targets = build_job_targets(postings)
        explanations: dict[str, dict[str, Any]] = {}
        for match in matches:
            target = ExplainableTarget(
                target_id=match.job.job_id,
                title=match.job.title,
                description=match.job.description,
                required_skills=list(match.job.required_skills),
                preferred_skills=list(match.job.preferred_skills),
                experience_level=match.job.experience_level,
                target_type="job",
            )
            explanations[match.job.job_id] = self._explain_target(
                resume_text=resume_text,
                resume_skills=resume_skills,
                target=target,
                background_targets=background_targets,
                observed_score=match.overall_score,
                semantic_score=match.semantic_score,
            )
        return explanations

    def explain_role_matches(
        self,
        resume_text: str,
        resume_skills: list[str],
        role_matches: list[RoleMatch],
    ) -> dict[str, dict[str, Any]]:
        if not role_matches:
            return {}

        background_targets = build_role_targets()
        explanations: dict[str, dict[str, Any]] = {}
        for role_match in role_matches:
            role_profile = get_job_role(role_match.role)
            required_skills = list(role_profile.core_skills) if role_profile else list(
                dict.fromkeys(role_match.matched_core + role_match.missing_core)
            )
            preferred_skills = list(role_profile.optional_skills) if role_profile else list(role_match.matched_optional)
            description = role_profile.description if role_profile else role_match.description
            target = ExplainableTarget(
                target_id=f"role::{role_match.role}",
                title=role_match.role,
                description=description,
                required_skills=required_skills,
                preferred_skills=preferred_skills,
                experience_level="Not specified",
                target_type="role",
            )
            explanations[role_match.role] = self._explain_target(
                resume_text=resume_text,
                resume_skills=resume_skills,
                target=target,
                background_targets=background_targets,
                observed_score=role_match.score,
                semantic_score=0.0,
            )
        return explanations

    def _explain_target(
        self,
        *,
        resume_text: str,
        resume_skills: list[str],
        target: ExplainableTarget,
        background_targets: list[ExplainableTarget],
        observed_score: float,
        semantic_score: float,
    ) -> dict[str, Any]:
        relevant_targets = self._select_background_targets(
            resume_text=resume_text,
            resume_skills=resume_skills,
            target=target,
            background_targets=background_targets,
        )
        skill_vocab = self._select_skill_vocab(resume_skills, target, relevant_targets)
        dataset = self._build_dataset(
            resume_text=resume_text,
            resume_skills=resume_skills,
            targets=relevant_targets,
            skill_vocab=skill_vocab,
        )

        target_features = self._featurize_pair(
            resume_text=resume_text,
            resume_skills=resume_skills,
            target=target,
            skill_vocab=skill_vocab,
            semantic_score=semantic_score,
            observed_score=observed_score,
        )

        try:
            explanation = self._fit_and_explain(dataset, target_features)
        except Exception:
            explanation = self._heuristic_explanation(target_features)

        explanation["target_title"] = target.title
        explanation["target_type"] = target.target_type
        explanation["match_score"] = round(float(observed_score), 1)
        explanation["semantic_score"] = round(float(semantic_score), 1)
        explanation["summary"] = self._build_summary(explanation)
        return explanation

    def _select_background_targets(
        self,
        *,
        resume_text: str,
        resume_skills: list[str],
        target: ExplainableTarget,
        background_targets: list[ExplainableTarget],
    ) -> list[ExplainableTarget]:
        scored: list[tuple[ExplainableTarget, float]] = []
        for candidate in background_targets:
            candidate_score = self._score_target(resume_text, resume_skills, candidate)[0]
            if candidate.target_id == target.target_id:
                candidate_score += 1000.0
            scored.append((candidate, candidate_score))

        scored.sort(key=lambda item: item[1], reverse=True)
        selected = [candidate for candidate, _ in scored[: self.config.max_background_targets]]
        if not any(candidate.target_id == target.target_id for candidate in selected):
            selected = [target] + selected[:-1]
        return selected

    def _select_skill_vocab(
        self,
        resume_skills: list[str],
        target: ExplainableTarget,
        background_targets: list[ExplainableTarget],
    ) -> list[str]:
        counter: Counter[str] = Counter()
        for skill in resume_skills:
            counter[skill.lower().strip()] += 3
        for skill in target.required_skills:
            counter[skill.lower().strip()] += 5
        for skill in target.preferred_skills:
            counter[skill.lower().strip()] += 2
        for candidate in background_targets[:100]:
            for skill in candidate.required_skills:
                counter[skill.lower().strip()] += 1
            for skill in candidate.preferred_skills:
                counter[skill.lower().strip()] += 1

        return [skill for skill, _ in counter.most_common(self.config.max_skill_features)]

    def _build_dataset(
        self,
        *,
        resume_text: str,
        resume_skills: list[str],
        targets: list[ExplainableTarget],
        skill_vocab: list[str],
    ) -> pd.DataFrame:
        rows = []
        for target in targets:
            score, semantic_score = self._score_target(resume_text, resume_skills, target)
            rows.append(
                self._featurize_pair(
                    resume_text=resume_text,
                    resume_skills=resume_skills,
                    target=target,
                    skill_vocab=skill_vocab,
                    semantic_score=semantic_score,
                    observed_score=score,
                )
            )
        return pd.DataFrame(rows)

    def _fit_and_explain(
        self,
        dataset: pd.DataFrame,
        target_features: dict[str, Any],
    ) -> dict[str, Any]:
        from sklearn.ensemble import RandomForestRegressor

        feature_frame = dataset.drop(columns=["target_score"])
        target_series = dataset["target_score"]
        feature_names = feature_frame.columns.tolist()

        model = RandomForestRegressor(
            n_estimators=160,
            max_depth=10,
            min_samples_leaf=2,
            random_state=self.config.random_state,
            n_jobs=-1,
        )
        model.fit(feature_frame, target_series)

        row = pd.DataFrame([{k: v for k, v in target_features.items() if k != "target_score"}])[feature_names]
        predicted_score = float(model.predict(row)[0])

        import shap

        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(row)
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
        if isinstance(shap_values, np.ndarray) and shap_values.ndim == 2:
            shap_values = shap_values[0]

        base_value = explainer.expected_value
        if isinstance(base_value, (list, tuple, np.ndarray)):
            base_value = float(np.asarray(base_value).flatten()[0])
        else:
            base_value = float(base_value)

        factor_rows = []
        for feature_name, impact in sorted(
            zip(feature_names, shap_values),
            key=lambda item: abs(float(item[1])),
            reverse=True,
        ):
            impact_value = round(float(impact), 2)
            if impact_value == 0:
                continue
            factor_rows.append(
                {
                    "feature": feature_name,
                    "label": self._display_label(feature_name),
                    "impact": impact_value,
                    "value": self._display_value(feature_name, row.iloc[0][feature_name]),
                }
            )

        positive_factors = [row for row in factor_rows if row["impact"] > 0][: self.config.top_factors]
        negative_factors = [row for row in factor_rows if row["impact"] < 0][: self.config.top_factors]

        return {
            "method": "shap",
            "base_value": round(base_value, 2),
            "predicted_score": round(predicted_score, 1),
            "positive_factors": positive_factors,
            "negative_factors": negative_factors,
            "feature_values": {
                key: value
                for key, value in target_features.items()
                if key
                in {
                    "matched_required_count",
                    "matched_preferred_count",
                    "missing_required_count",
                    "required_match_pct",
                    "preferred_match_pct",
                    "experience_score",
                    "semantic_score",
                }
            },
        }

    def _heuristic_explanation(self, target_features: dict[str, Any]) -> dict[str, Any]:
        positive_factors = []
        negative_factors = []

        required_matches = max(int(target_features.get("matched_required_count", 0)), 0)
        preferred_matches = max(int(target_features.get("matched_preferred_count", 0)), 0)
        missing_required = max(int(target_features.get("missing_required_count", 0)), 0)
        experience_score = float(target_features.get("experience_score", 0.0))

        for feature_name, value in target_features.items():
            if not isinstance(value, (int, float)):
                continue
            if feature_name.startswith("match_skill_") and value >= 1:
                impact = round(40.0 / max(required_matches, 1), 2)
                positive_factors.append(
                    {
                        "feature": feature_name,
                        "label": self._display_label(feature_name),
                        "impact": impact,
                        "value": "present",
                    }
                )
            elif feature_name.startswith("preferred_skill_") and value >= 1:
                impact = round(12.0 / max(preferred_matches, 1), 2)
                positive_factors.append(
                    {
                        "feature": feature_name,
                        "label": self._display_label(feature_name),
                        "impact": impact,
                        "value": "present",
                    }
                )
            elif feature_name.startswith("missing_skill_") and value >= 1:
                impact = -round(40.0 / max(missing_required, 1), 2)
                negative_factors.append(
                    {
                        "feature": feature_name,
                        "label": self._display_label(feature_name),
                        "impact": impact,
                        "value": "missing",
                    }
                )

        positive_factors.append(
            {
                "feature": "required_match_pct",
                "label": "Required skill coverage",
                "impact": round(float(target_features.get("required_match_pct", 0.0)) * 0.2, 2),
                "value": f"{float(target_features.get('required_match_pct', 0.0)):.1f}%",
            }
        )
        positive_factors.append(
            {
                "feature": "experience_score",
                "label": "Experience alignment",
                "impact": round((experience_score - 50.0) * 0.1, 2),
                "value": f"{experience_score:.1f}%",
            }
        )
        negative_factors.append(
            {
                "feature": "missing_required_count",
                "label": "Missing required skills",
                "impact": -round(float(missing_required) * 6.0, 2),
                "value": int(missing_required),
            }
        )

        positive_factors = sorted(positive_factors, key=lambda row: abs(row["impact"]), reverse=True)[
            : self.config.top_factors
        ]
        negative_factors = sorted(negative_factors, key=lambda row: abs(row["impact"]), reverse=True)[
            : self.config.top_factors
        ]

        predicted_score = float(target_features.get("target_score", 0.0))
        return {
            "method": "heuristic",
            "base_value": 0.0,
            "predicted_score": round(predicted_score, 1),
            "positive_factors": positive_factors,
            "negative_factors": negative_factors,
            "feature_values": {
                "matched_required_count": int(target_features.get("matched_required_count", 0)),
                "matched_preferred_count": int(target_features.get("matched_preferred_count", 0)),
                "missing_required_count": int(target_features.get("missing_required_count", 0)),
                "required_match_pct": float(target_features.get("required_match_pct", 0.0)),
                "preferred_match_pct": float(target_features.get("preferred_match_pct", 0.0)),
                "experience_score": float(target_features.get("experience_score", 0.0)),
                "semantic_score": float(target_features.get("semantic_score", 0.0)),
            },
        }

    def _featurize_pair(
        self,
        *,
        resume_text: str,
        resume_skills: list[str],
        target: ExplainableTarget,
        skill_vocab: list[str],
        semantic_score: float,
        observed_score: float,
    ) -> dict[str, Any]:
        resume_set = {skill.lower().strip() for skill in resume_skills}
        required_set = {skill.lower().strip() for skill in target.required_skills}
        preferred_set = {skill.lower().strip() for skill in target.preferred_skills}

        matched_required = resume_set & required_set
        matched_preferred = resume_set & preferred_set
        missing_required = required_set - resume_set

        required_match_pct = (
            len(matched_required) / len(required_set) * 100.0 if required_set else 100.0
        )
        preferred_match_pct = (
            len(matched_preferred) / len(preferred_set) * 100.0 if preferred_set else 0.0
        )
        experience_score = _experience_score(resume_text, target.experience_level) * 100.0

        features: dict[str, Any] = {
            "resume_skill_count": len(resume_set),
            "required_skill_count": len(required_set),
            "preferred_skill_count": len(preferred_set),
            "matched_required_count": len(matched_required),
            "matched_preferred_count": len(matched_preferred),
            "missing_required_count": len(missing_required),
            "required_match_pct": round(required_match_pct, 4),
            "preferred_match_pct": round(preferred_match_pct, 4),
            "overall_skill_coverage_pct": round(
                ((len(matched_required) + len(matched_preferred))
                / max(len(required_set) + len(preferred_set), 1))
                * 100.0,
                4,
            ),
            "experience_score": round(experience_score, 4),
            "semantic_score": round(float(semantic_score), 4),
            "description_length": len(target.description.split()),
            "target_score": round(float(observed_score), 4),
        }

        for skill in skill_vocab:
            token = self._feature_token(skill)
            features[f"match_skill_{token}"] = 1 if skill in matched_required else 0
            features[f"missing_skill_{token}"] = 1 if skill in missing_required else 0
            features[f"preferred_skill_{token}"] = 1 if skill in matched_preferred else 0
            features[f"resume_has_{token}"] = 1 if skill in resume_set else 0
            features[f"target_requires_{token}"] = 1 if skill in required_set else 0

        return features

    def _score_target(
        self,
        resume_text: str,
        resume_skills: list[str],
        target: ExplainableTarget,
    ) -> tuple[float, float]:
        resume_set = {skill.lower().strip() for skill in resume_skills}
        required_set = {skill.lower().strip() for skill in target.required_skills}
        preferred_set = {skill.lower().strip() for skill in target.preferred_skills}

        matched_required = resume_set & required_set
        matched_preferred = resume_set & preferred_set

        required_match_pct = (len(matched_required) / len(required_set) * 100.0) if required_set else 100.0
        preferred_match_pct = (len(matched_preferred) / len(preferred_set) * 100.0) if preferred_set else 0.0
        skill_score = required_match_pct * 0.7 + preferred_match_pct * 0.3
        experience_score = _experience_score(resume_text, target.experience_level) * 100.0
        semantic_score = 0.0

        if target.target_type == "job":
            overall_score = skill_score * 0.8 + experience_score * 0.2
        else:
            overall_score = skill_score

        return round(float(overall_score), 4), semantic_score

    @staticmethod
    def _feature_token(skill: str) -> str:
        safe = "".join(ch.lower() if ch.isalnum() else "_" for ch in skill.strip())
        while "__" in safe:
            safe = safe.replace("__", "_")
        return safe.strip("_")

    @staticmethod
    def _display_label(feature_name: str) -> str:
        if feature_name.startswith("match_skill_"):
            return f"Matched required skill: {feature_name.removeprefix('match_skill_').replace('_', ' ').title()}"
        if feature_name.startswith("missing_skill_"):
            return f"Missing required skill: {feature_name.removeprefix('missing_skill_').replace('_', ' ').title()}"
        if feature_name.startswith("preferred_skill_"):
            return f"Matched optional skill: {feature_name.removeprefix('preferred_skill_').replace('_', ' ').title()}"
        if feature_name.startswith("resume_has_"):
            return f"Resume includes: {feature_name.removeprefix('resume_has_').replace('_', ' ').title()}"
        if feature_name.startswith("target_requires_"):
            return f"Role requires: {feature_name.removeprefix('target_requires_').replace('_', ' ').title()}"
        mapping = {
            "matched_required_count": "Matched required skills",
            "matched_preferred_count": "Matched optional skills",
            "missing_required_count": "Missing required skills",
            "required_match_pct": "Required skill coverage",
            "preferred_match_pct": "Optional skill coverage",
            "overall_skill_coverage_pct": "Overall skill coverage",
            "experience_score": "Experience alignment",
            "semantic_score": "Semantic similarity",
            "resume_skill_count": "Resume skill breadth",
            "required_skill_count": "Required skill count",
            "preferred_skill_count": "Optional skill count",
            "description_length": "Description richness",
        }
        return mapping.get(feature_name, feature_name.replace("_", " ").title())

    @staticmethod
    def _display_value(feature_name: str, value: Any) -> str:
        if isinstance(value, (int, np.integer)):
            return str(int(value))
        if isinstance(value, (float, np.floating)):
            if feature_name.endswith("_pct") or feature_name.endswith("_score"):
                return f"{float(value):.1f}%"
            return f"{float(value):.2f}"
        return str(value)

    def _build_summary(self, explanation: dict[str, Any]) -> str:
        positive = explanation.get("positive_factors", [])
        negative = explanation.get("negative_factors", [])

        positive_text = ", ".join(row["label"] for row in positive[:2]) or "resume-job alignment"
        negative_text = ", ".join(row["label"] for row in negative[:2]) or "few penalties"
        predicted = explanation.get("predicted_score", explanation.get("match_score", 0.0))
        method = explanation.get("method", "heuristic").upper()

        return (
            f"{method} explanation estimates a {predicted:.1f}% fit. "
            f"The strongest positive drivers were {positive_text}. "
            f"The biggest drag came from {negative_text}."
        )
