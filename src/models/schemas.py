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
    proficiency: str = "intermediate"  # basic / intermediate / advanced / expert
    proficiency_score: float = 0.6
    proficiency_evidence: list[str] = Field(default_factory=list)
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


class PortfolioRepository(BaseModel):
    name: str
    url: str = ""
    description: str = ""
    primary_language: str = ""
    languages: list[str] = Field(default_factory=list)
    stars: int = 0
    forks: int = 0
    size_kb: int = 0
    pushed_at: Optional[str] = None
    topics: list[str] = Field(default_factory=list)


class PortfolioSkillEvidence(BaseModel):
    skill: str
    status: str = "unverified"  # verified / partial / unverified
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class PortfolioReport(BaseModel):
    github_username: Optional[str] = None
    profile_url: Optional[str] = None
    portfolio_score: float = 0.0
    activity_score: float = 0.0
    complexity_score: float = 0.0
    documentation_score: float = 0.0
    impact_score: float = 0.0
    verified_skills: list[PortfolioSkillEvidence] = Field(default_factory=list)
    weak_skills: list[PortfolioSkillEvidence] = Field(default_factory=list)
    repositories: list[PortfolioRepository] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    summary: str = ""
    source_status: str = "not_checked"  # not_checked / api_live / resume_only / api_unavailable


class InterviewQuestion(BaseModel):
    skill: str
    category: str = "technical"  # technical / practical / scenario / behavioral
    difficulty: str = "mid"  # junior / mid / senior
    question: str
    expected_points: list[str] = Field(default_factory=list)


class InterviewAnswerEvaluation(BaseModel):
    correctness: float = 0.0
    completeness: float = 0.0
    clarity: float = 0.0
    overall: float = 0.0
    feedback: str = ""
    missing_points: list[str] = Field(default_factory=list)


class InterviewPrepReport(BaseModel):
    target_role: str
    success_probability: float = 0.0
    readiness_level: str = "Developing"
    focus_skills: list[str] = Field(default_factory=list)
    questions: list[InterviewQuestion] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    summary: str = ""
    source_status: str = "rule_based"  # rule_based / groq


class LearningAssessmentQuestion(BaseModel):
    skill: str
    difficulty: str = "intermediate"
    prompt: str
    expected_points: list[str] = Field(default_factory=list)
    question_type: str = "short_answer"  # short_answer / scenario / checklist


class LearningCheckpoint(BaseModel):
    skill: str
    milestone_label: str = ""
    target_weeks: int = 4
    target_score: float = 70.0
    estimated_hours: int = 12
    assessment_focus: list[str] = Field(default_factory=list)
    practice_evidence: list[str] = Field(default_factory=list)
    questions: list[LearningAssessmentQuestion] = Field(default_factory=list)


class LearningAssessmentResult(BaseModel):
    skill: str
    theory_score: float = 0.0
    practical_score: float = 0.0
    overall_score: float = 0.0
    readiness_level: str = "Developing"
    checkpoint_status: str = "behind"  # behind / on_track / ready
    feedback: str = ""
    strengths: list[str] = Field(default_factory=list)
    missing_points: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class ContinuousLearningReport(BaseModel):
    target_role: str
    summary: str = ""
    checkpoints: list[LearningCheckpoint] = Field(default_factory=list)
    focus_skills: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    source_status: str = "rule_based"


class CareerTrajectoryPath(BaseModel):
    role: str
    domain: str = ""
    current_match_score: float = 0.0
    projected_match_after_learning: float = 0.0
    salary_year_1_lpa: float = 0.0
    salary_year_3_lpa: float = 0.0
    salary_year_5_lpa: float = 0.0
    growth_rate_pct: float = 0.0
    success_probability: float = 0.0
    risk_level: str = "Moderate"
    roi_score: float = 0.0
    top_missing_skills: list[str] = Field(default_factory=list)
    recommendation: str = ""


class CareerTrajectoryReport(BaseModel):
    summary: str = ""
    recommended_path: str = ""
    paths: list[CareerTrajectoryPath] = Field(default_factory=list)
    source_status: str = "heuristic"


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
