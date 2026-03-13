"""
SHAP Explainability Module
==========================
Uses a lightweight Random Forest surrogate trained on resume-job feature
vectors, then applies SHAP TreeExplainer to produce per-skill feature
importance values.

Public API
----------
    explainer = SHAPExplainer(skill_vocab)
    explainer.fit(training_pairs)
    explanation = explainer.explain(resume_skills, match_result)
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from src.config.settings import SKILLS_VOCAB_PATH


class SHAPExplainer:
    """
    Wraps a Random Forest surrogate + SHAP TreeExplainer
    to explain *why* a job was matched.
    """

    def __init__(self, vocab: Optional[list[str]] = None):
        if vocab is None:
            vocab = pd.read_csv(SKILLS_VOCAB_PATH)["skill"].str.lower().tolist()
        self.vocab: list[str] = vocab[:60]  # top-60 skills for feature vector
        self.model: Optional[RandomForestClassifier] = None
        self.explainer = None  # shap.TreeExplainer (lazy)
        self._feature_names: list[str] = []

    # ------------------------------------------------------------------ fit
    def fit(self, pairs: list[dict]) -> float:
        """
        Train the surrogate model.

        *pairs* is a list of dicts, each with keys:
            ``resume_skills``  – list[str]
            ``job_required``   – list[str]
            ``job_preferred``  – list[str]
            ``label``          – 1 (good) / 0 (bad)
        Returns test accuracy.
        """
        rows = [self._featurize(p) for p in pairs]
        df = pd.DataFrame(rows)
        y = df.pop("label")
        self._feature_names = df.columns.tolist()

        from sklearn.model_selection import train_test_split

        X_train, X_test, y_train, y_test = train_test_split(
            df, y, test_size=0.2, random_state=42
        )
        self.model = RandomForestClassifier(
            n_estimators=120, max_depth=12, random_state=42, n_jobs=-1
        )
        self.model.fit(X_train, y_train)
        acc = self.model.score(X_test, y_test)

        import shap

        self.explainer = shap.TreeExplainer(self.model)
        return acc

    # ------------------------------------------------------------- explain
    def explain(
        self,
        resume_skills: list[str],
        job_required: list[str],
        job_preferred: list[str],
    ) -> dict:
        """
        Return SHAP explanation dict::

            {
                "top_positive": [("python", +0.25), ...],
                "top_negative": [("docker", -0.08), ...],
                "base_value": float,
                "prediction_prob": float,
            }
        """
        if self.model is None or self.explainer is None:
            # Fallback heuristic explanation when model hasn't been trained
            return self._heuristic_explain(resume_skills, job_required, job_preferred)

        feat = self._featurize(
            {
                "resume_skills": resume_skills,
                "job_required": job_required,
                "job_preferred": job_preferred,
                "label": 0,
            }
        )
        feat.pop("label", None)
        X = pd.DataFrame([feat])[self._feature_names]
        shap_values = self.explainer.shap_values(X)
        if isinstance(shap_values, list):
            shap_values = shap_values[1]
        importance = sorted(
            zip(self._feature_names, shap_values[0]),
            key=lambda t: abs(t[1]),
            reverse=True,
        )
        return {
            "top_positive": [(f, round(float(v), 4)) for f, v in importance if v > 0][
                :10
            ],
            "top_negative": [(f, round(float(v), 4)) for f, v in importance if v < 0][
                :10
            ],
            "base_value": float(
                self.explainer.expected_value[1]
                if isinstance(self.explainer.expected_value, (list, np.ndarray))
                else self.explainer.expected_value
            ),
            "prediction_prob": float(self.model.predict_proba(X)[0][1]),
        }

    # -------------------------------------------------------- featurize
    def _featurize(self, pair: dict) -> dict:
        resume_set = {s.lower() for s in pair["resume_skills"]}
        req_set = {s.lower() for s in pair["job_required"]}
        pref_set = {s.lower() for s in pair["job_preferred"]}

        feat: dict = {
            "num_resume_skills": len(resume_set),
            "num_required": len(req_set),
            "num_preferred": len(pref_set),
            "matched_required": len(resume_set & req_set),
            "matched_preferred": len(resume_set & pref_set),
            "missing_required": len(req_set - resume_set),
            "req_match_pct": (
                len(resume_set & req_set) / len(req_set) * 100 if req_set else 0
            ),
            "pref_match_pct": (
                len(resume_set & pref_set) / len(pref_set) * 100 if pref_set else 0
            ),
        }

        for skill in self.vocab:
            sl = skill.lower()
            feat[f"resume_has_{sl.replace(' ', '_')}"] = 1 if sl in resume_set else 0
            feat[f"job_req_{sl.replace(' ', '_')}"] = 1 if sl in req_set else 0

        feat["label"] = pair.get("label", 0)
        return feat

    # ------------------------------------------------- heuristic fallback
    @staticmethod
    def _heuristic_explain(
        resume_skills: list[str],
        job_required: list[str],
        job_preferred: list[str],
    ) -> dict:
        resume_set = {s.lower() for s in resume_skills}
        req_set = {s.lower() for s in job_required}
        pref_set = {s.lower() for s in job_preferred}

        num_req = max(len(req_set), 1)
        num_pref = max(len(pref_set), 1)

        positives = []
        for s in sorted(resume_set & req_set):
            positives.append((s, round(0.70 / num_req, 4)))
        for s in sorted(resume_set & pref_set):
            positives.append((s, round(0.30 / num_pref, 4)))

        negatives = []
        for s in sorted(req_set - resume_set):
            negatives.append((s, round(-0.70 / num_req, 4)))

        return {
            "top_positive": sorted(positives, key=lambda t: -t[1])[:10],
            "top_negative": sorted(negatives, key=lambda t: t[1])[:10],
            "base_value": 0.5,
            "prediction_prob": len(resume_set & req_set) / num_req if req_set else 0.0,
        }
