"""
Pydantic schemas for the FAIR-PATH platform.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ── Skill models ───────────────────────────────────────────────────────
class ExtractedSkill(BaseModel):
    name: str
    canonical: str  # normalised / deduplicated name
    source_section: str = "unknown"  # Skills, Experience, Projects, etc.
    proficiency: str = "intermediate"  # basic / intermediate / advanced
    confidence: float = 1.0


class ResumeParseResult(BaseModel):
    text: str
    email: Optional[str] = None
    phone: Optional[str] = None
    experience_years: Optional[int] = None


class SkillGap(BaseModel):
    skill: str
    job_count: int = 0
    demand_pct: float = 0.0
    priority: str = "Medium"  # High / Medium / Low


# ── Job models ─────────────────────────────────────────────────────────
class JobPosting(BaseModel):
    job_id: str
    title: str
    company: str = "Unknown"
    description: str = ""
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    location: str = "Unknown"
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    remote: bool = False
    experience_level: str = "Not specified"
    posted_date: Optional[str] = None
    source: str = "static"


# ── Match / explainability ─────────────────────────────────────────────
class SkillContribution(BaseModel):
    skill: str
    impact: float
    kind: str = "required"  # required / preferred / missing / semantic


class MatchResult(BaseModel):
    job: JobPosting
    overall_score: float = 0.0
    semantic_score: float = 0.0
    skill_score: float = 0.0
    experience_score: float = 0.0
    matched_required: list[str] = Field(default_factory=list)
    matched_preferred: list[str] = Field(default_factory=list)
    missing_required: list[str] = Field(default_factory=list)
    skill_contributions: list[SkillContribution] = Field(default_factory=list)
    shap_values: dict = Field(default_factory=dict)


# ── Fairness ───────────────────────────────────────────────────────────
class BiasIndicator(BaseModel):
    word: str
    category: str
    occurrences: int = 1
    penalty: float = 0.0
    description: str = ""


class FairnessReport(BaseModel):
    score: float = 100.0
    gender_bias: str = "None detected"
    age_bias: str = "None detected"
    education_bias: str = "None detected"
    experience_bias: str = "None detected"
    indicators: list[BiasIndicator] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    mitigation_applied: bool = False
    mitigated_score: float = 100.0
    demographic_parity_difference: float = 0.0
    variant_scores: dict[str, float] = Field(default_factory=dict)
    anonymized_text_preview: str = ""


# ── Trend ──────────────────────────────────────────────────────────────
class SkillTrend(BaseModel):
    skill: str
    current_count: int = 0
    current_pct: float = 0.0
    growth_pct: float = 0.0  # +40 %, -10 %, etc.
    forecast_demand: str = "Stable"


# ── API request / response ─────────────────────────────────────────────
class ResumeAnalysisRequest(BaseModel):
    resume_text: str
    top_n: int = 20
    min_score: float = 0.0
    remote_only: bool = False


class ResumeAnalysisResponse(BaseModel):
    skills: list[ExtractedSkill]
    matches: list[MatchResult]
    skill_gaps: list[SkillGap]
    trends: list[SkillTrend]
    fairness: FairnessReport
