"""
FAIR-PATH v2 — AI Career Intelligence Platform
================================================
Streamlit frontend that orchestrates every backend module:
    • Skill extraction  (RoBERTa NER + dictionary)
    • Semantic matching  (Sentence-BERT)
    • SHAP explainability
    • Skill gap ranking
    • Trend forecasting
    • Fairness detection
"""
from __future__ import annotations

import os
import sys
import tempfile
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------------------------
# Ensure root package is importable
# ---------------------------------------------------------------------------
_ROOT = str(Path(__file__).resolve().parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.config.settings import (
    JOBS_PARSED_PATH,
    SKILL_CATEGORIES,
)
from src.career_trajectory_simulator import simulate_career_trajectories
from src.continuous_learning_validator import (
    build_learning_validation_report,
    evaluate_learning_checkpoint,
)
from src.job_roles_database import get_job_role
from src.portfolio_analyzer import analyze_portfolio
from src.report_exporter import build_executive_summary, build_markdown_report
from src.interview_preparation_agent import evaluate_mock_answer, generate_interview_prep
from src.fairness.detector import evaluate_fairness
from src.models.schemas import (
    CareerTrajectoryReport,
    ContinuousLearningReport,
    ExtractedSkill,
    FairnessReport,
    InterviewPrepReport,
    PortfolioReport,
    ResumeParseResult,
    SkillGap,
    SkillTrend,
)
from src.role_mapping.matcher import match_roles, RoleMatch
from src.resume_parser import parse_resume
from src.shap_explainer import MatchSHAPExplainer
from src.skill_extractor import extract_skills
from src.skill_gap.ranker import rank_skill_gaps
from src.learning_path_visualizer import render_learning_path
<<<<<<< HEAD
from src.temporal_job_dynamics import analyze_role_temporal_dynamics
=======
>>>>>>> 762d549ff5cab1fc93bc6825be5008a3d4e0034c
from src.trend_forecaster import get_skill_trends, get_trends_for_skills

# New comprehensive gap analysis
try:
    from src.skill_gap_analysis import SkillGapAnalysis
    HAS_GAP_ANALYSIS = True
except ImportError:
    HAS_GAP_ANALYSIS = False


# ---------------------------------------------------------------------------
# Cached loaders — run only once across reruns
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Loading job database…")
def _cached_load_jobs():
    if os.path.exists(JOBS_PARSED_PATH):
        return pd.read_csv(JOBS_PARSED_PATH, nrows=2000)
    return pd.DataFrame()


@st.cache_resource(show_spinner="Loading comprehensive gap analysis…")
def _load_gap_analyzer():
    """Pre-load comprehensive gap analysis system."""
    if not HAS_GAP_ANALYSIS:
        return None
    try:
        from src.skill_gap_analysis import SkillGapAnalysis
        analyzer = SkillGapAnalysis()
        return analyzer
    except Exception as e:
        import traceback
        print(f"Warning: Could not load advanced gap analysis: {e}")
        print(traceback.format_exc())
        return None

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="FAIR-PATH: AI Career Intelligence",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
    .stApp {
        background:
            radial-gradient(circle at top right, rgba(46, 204, 113, 0.10), transparent 24%),
            radial-gradient(circle at top left, rgba(31, 119, 180, 0.10), transparent 28%),
            linear-gradient(180deg, #f7fbff 0%, #ffffff 45%, #f8fafc 100%);
    }
    .main-header {
        font-size: 2.75rem; font-weight: 800;
        background: linear-gradient(120deg, #0f4c81, #149f6f);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; margin-bottom: .25rem; letter-spacing: -.02em;
    }
    .subtitle {
        text-align:center; color:#52606d; font-size:1.05rem; margin-bottom:1.4rem;
        max-width: 900px; margin-left: auto; margin-right: auto;
    }
    .metric-card {
        background: rgba(255,255,255,0.88); border-radius: 14px; padding: 1rem 1.2rem;
        border: 1px solid rgba(15, 76, 129, 0.10); box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
        margin-bottom: .7rem;
    }
    .skill-chip {
        display: inline-block; padding: 4px 12px; margin: 3px;
        border-radius: 16px; font-size: .85rem; font-weight: 500;
    }
    .chip-advanced  { background:#d4edda; color:#155724; }
    .chip-intermediate { background:#cce5ff; color:#004085; }
    .chip-basic     { background:#fff3cd; color:#856404; }
    .priority-high   { color:#dc3545; font-weight:700; }
    .priority-medium { color:#fd7e14; font-weight:700; }
    .priority-low    { color:#28a745; font-weight:700; }
    .score-bar { height:22px; border-radius:6px; }
    .surface-card {
        background: rgba(255,255,255,0.92);
        border: 1px solid rgba(15, 23, 42, 0.08);
        border-radius: 16px;
        padding: 16px 18px;
        box-shadow: 0 12px 34px rgba(15, 23, 42, 0.07);
        margin-bottom: 0.8rem;
    }
    .surface-title {
        font-size: 1rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.35rem;
    }
    .surface-copy {
        color: #475569;
        font-size: 0.92rem;
        line-height: 1.5;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown('<div class="main-header">FAIR-PATH v2</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">AI-Powered Career Intelligence &mdash; '
    "Role-first resume intelligence with proficiency-aware matching, portfolio validation, interview preparation, learning paths, trends, and fairness checks.</div>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def _init_state():
    for key in (
        "resume_text",
        "resume_profile",
        "skills",
        "role_matches",
        "gaps",
        "trends",
        "fairness",
        "portfolio_report",
        "interview_prep",
        "learning_validation",
        "career_trajectory",
        "temporal_dynamics",
        "comprehensive_gap_analysis",
        "role_explanations",
    ):
        if key not in st.session_state:
            st.session_state[key] = None


_init_state()


def _render_mermaid_diagram(diagram: str, height: int = 520) -> None:
    if not diagram.strip():
        return

    escaped_diagram = escape(diagram)
    mermaid_html = f"""
    <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:16px;padding:16px;">
      <div class="mermaid">
      {escaped_diagram}
      </div>
    </div>
    <script type="module">
      import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
      mermaid.initialize({{
        startOnLoad: true,
        securityLevel: "loose",
        theme: "default",
        flowchart: {{
          curve: "basis",
          useMaxWidth: true
        }}
      }});
    </script>
    """
    components.html(mermaid_html, height=height, scrolling=False)

# Heavy resources are loaded lazily during analysis to keep startup fast.
_jobs_df = None
_gap_analyzer = None


# ---------------------------------------------------------------------------
# Sidebar — upload + options
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Upload Resume")
    uploaded = st.file_uploader(
        "PDF, DOCX, or TXT",
        type=["pdf", "docx", "txt"],
        help="Upload your resume to begin analysis.",
    )
    st.divider()
<<<<<<< HEAD
    st.subheader("Options")
=======
    st.subheader("⚙️ Options")
>>>>>>> 762d549ff5cab1fc93bc6825be5008a3d4e0034c
    use_ner = st.toggle("Use NER extraction", value=False, help="RoBERTa NER improves extraction but makes analysis slower.")
    top_n = st.slider("Top N role suggestions", 5, 30, 10)
    min_score = st.slider("Minimum match score", 0, 80, 10, step=5)
    
    st.divider()
    st.subheader("Learning Preferences")
    experience_level = st.selectbox(
        "Your Experience Level",
        ["beginner", "intermediate", "advanced"],
        help="Used to personalize learning path difficulty and pace"
    )
    available_time = st.selectbox(
        "Time to Dedicate",
        ["part-time (2 hrs/day)", "full-time (6-8 hrs/day)", "minimal (1 hr/day)"],
        help="Affects learning timeline and curriculum density"
    )
    learning_style = st.selectbox(
        "Preferred Learning Style",
        ["hands-on (projects)", "theory-first (courses)", "mixed"],
        help="Influences resource recommendations"
    )
    budget = st.selectbox(
        "Budget for Learning",
        ["free only", "budget-friendly (<$100)", "willing-to-invest"],
        help="Filters course recommendations"
    )
    github_profile_input = st.text_input(
        "GitHub profile URL (optional)",
        value="",
        help="Optional manual GitHub profile link for portfolio validation.",
    )

    st.divider()
    run_btn = st.button("Analyse Resume", type="primary", width="stretch")

    st.markdown("---")
    st.caption("FAIR-PATH v2.0 — AI Career Intelligence")

# ---------------------------------------------------------------------------
# Main analysis pipeline
# ---------------------------------------------------------------------------

if run_btn and uploaded is not None:
    if _jobs_df is None:
        _jobs_df = _cached_load_jobs()
    if _gap_analyzer is None and HAS_GAP_ANALYSIS:
        _gap_analyzer = _load_gap_analyzer()

    with st.status("Running full analysis…", expanded=True) as status:
        # 1 — Extract text
        st.write("Extracting text...")
        ext = os.path.splitext(uploaded.name)[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext or ".pdf") as tmp:
            tmp.write(uploaded.getvalue())
            tmp_path = tmp.name
        try:
            parsed_resume = parse_resume(tmp_path, filename=uploaded.name)
        finally:
            os.unlink(tmp_path)

        text = parsed_resume.text
        if not text or len(text.strip()) < 30:
            st.error("Could not extract meaningful text from the file.")
            st.stop()
        st.session_state.resume_text = text
        st.session_state.resume_profile = parsed_resume

        # 2 — Skill extraction
        st.write("Extracting skills...")
        skills = extract_skills(text, use_ner=use_ner)
        st.session_state.skills = skills
        skill_names = [s.canonical for s in skills]

        # 3 — Role mapping
        st.write("Mapping suitable job roles...")
        role_matches = match_roles(
            skill_names,
            extracted_skills=skills,
            resume_text=text,
            min_score=min_score,
            top_n=top_n,
        )
        st.session_state.role_matches = role_matches

        # 4 — SHAP explainability
        st.write("Building SHAP explanations...")
        try:
            explainer = MatchSHAPExplainer()
<<<<<<< HEAD
=======
            st.session_state.match_explanations = explainer.explain_job_matches(
                text,
                skill_names,
                matches[:3],
                postings,
            )
>>>>>>> 762d549ff5cab1fc93bc6825be5008a3d4e0034c
            st.session_state.role_explanations = explainer.explain_role_matches(
                text,
                skill_names,
                role_matches[:3],
            )
        except Exception as exc:
            st.warning(f"Explainability fallback activated: {str(exc)[:180]}")
            st.session_state.role_explanations = {}

        # 5 — Portfolio analysis
        st.write("Analyzing portfolio evidence...")
        st.session_state.portfolio_report = analyze_portfolio(
            resume_text=text,
            extracted_skills=skills,
            github_profile=github_profile_input,
        )

        st.write("Preparing interview practice...")
        weak_portfolio_skills = [
            item.skill for item in (st.session_state.portfolio_report.weak_skills if st.session_state.portfolio_report else [])
        ]
        interview_missing_skills = []
        if role_matches:
            interview_missing_skills = role_matches[0].missing_core[:5]
        st.session_state.interview_prep = generate_interview_prep(
            target_role=role_matches[0].role if role_matches else "Target Role",
            match_score=role_matches[0].score if role_matches else 0.0,
            missing_skills=interview_missing_skills,
            weak_skills=weak_portfolio_skills[:3],
            portfolio_score=(st.session_state.portfolio_report.portfolio_score if st.session_state.portfolio_report else 0.0),
        )

        # 6 — Skill gaps
        st.write("Analysing skill gaps...")
        if _jobs_df is not None and not _jobs_df.empty:
            gaps = rank_skill_gaps(skill_names, _jobs_df, top_n=15)
            trends = get_skill_trends(_jobs_df)
        else:
            gaps = []
            trends = []
        st.session_state.gaps = gaps
        st.session_state.trends = trends

        st.write("Simulating career trajectories...")
        st.session_state.career_trajectory = simulate_career_trajectories(
            role_matches=role_matches,
            trends=trends,
            current_experience_years=parsed_resume.experience_years,
        )

        st.write("Forecasting temporal role dynamics...")
        temporal_dynamics = None
        if _jobs_df is not None and not _jobs_df.empty and role_matches:
            top_role_profile = get_job_role(role_matches[0].role)
            if top_role_profile is not None:
                temporal_dynamics = analyze_role_temporal_dynamics(
                    _jobs_df,
                    role_profile=top_role_profile,
                    user_skills=skill_names,
                    current_match_score=role_matches[0].score,
                )
        st.session_state.temporal_dynamics = temporal_dynamics

        # 5b — Comprehensive skill gap analysis
        st.write("Running comprehensive gap analysis...")
        comprehensive_analysis = None
        try:
            # Try to use cached analyzer first
            if _gap_analyzer is not None:
                analyzer_to_use = _gap_analyzer
                st.write("Using cached analyzer...")
            else:
                # If not cached, try to load it now
                st.write("Loading gap analyzer...")
                from src.skill_gap_analysis import SkillGapAnalysis
                analyzer_to_use = SkillGapAnalysis()
            
            # Run analysis only if we have role matches and skills
            if role_matches and skill_names and analyzer_to_use:
                st.write("Computing priority rankings, learning paths, and quick wins...")
                top_role = role_matches[0]
                top_role_profile = get_job_role(top_role.role)
                job_data = {
                    'role': top_role.role,
                    'description': (top_role_profile.description if top_role_profile else top_role.description),
                    'core_skills': list(top_role_profile.core_skills) if top_role_profile else list(set(top_role.matched_core + top_role.missing_core)),
                    'optional_skills': list(top_role_profile.optional_skills) if top_role_profile else list(set(top_role.matched_optional)),
                    'match_score': top_role.score,
                }
                
                # Build user context from sidebar preferences
                user_context = {
                    "experience_level": experience_level,
                    "available_time": available_time.split()[0],  # "part-time" from "part-time (2 hrs/day)"
                    "learning_style": learning_style.split()[0],  # "hands-on" from "hands-on (projects)"
                    "budget": budget.split()[0]  # "free" from "free only"
                }
                trend_map = {
                    trend.skill.lower(): {
                        "growth_rate": trend.growth_pct,
                        "trend": trend.forecast_demand,
                        "current_pct": trend.current_pct,
                    }
                    for trend in trends
                }
                
                comprehensive_analysis = analyzer_to_use.analyze_for_job(
                    user_skills=skill_names,
                    job_data=job_data,
                    current_match_score=top_role.score,
                    user_context=user_context,
                    trend_data=trend_map,
                )
                st.session_state.comprehensive_gap_analysis = comprehensive_analysis
                st.write("Comprehensive analysis complete.")
            else:
                st.write("Skipping comprehensive gap analysis because matched roles or skills are unavailable.")
        except Exception as e:
            import traceback
            st.error(f"Gap analysis error: {str(e)[:200]}")
            if st.checkbox("Show full error trace"):
                st.code(traceback.format_exc())

        st.write("Preparing learning validation checkpoints...")
        learning_validation = None
        if role_matches:
            source_learning_path = comprehensive_analysis.get("learning_path") if comprehensive_analysis else None
            source_priorities = comprehensive_analysis.get("ranked_priorities") if comprehensive_analysis else None
            learning_validation = build_learning_validation_report(
                target_role=role_matches[0].role,
                learning_path=source_learning_path,
                ranked_priorities=source_priorities,
            )
        st.session_state.learning_validation = learning_validation

        # 7 — Trends
        st.write("Computing trends...")

        # 8 — Fairness
        st.write("Evaluating fairness...")
        fairness = evaluate_fairness(text)
        st.session_state.fairness = fairness

        status.update(label="Analysis complete!", state="complete", expanded=False)

elif run_btn and uploaded is None:
    st.warning("Please upload a resume first.")

# ---------------------------------------------------------------------------
# Render results — tabbed layout
# ---------------------------------------------------------------------------

if st.session_state.skills is not None:
    tab_summary, tab_skills, tab_roles, tab_portfolio, tab_interview, tab_validate, tab_career, tab_gaps, tab_trends, tab_fair, tab_raw = st.tabs(
        ["Summary", "Skills", "Suitable Roles", "Portfolio", "Interview Prep", "Learning Validator", "Career Paths", "Skill Gaps", "Trends", "Fairness", "Resume Text"]
    )

    # ── TAB: Skills ────────────────────────────────────────────────────
    with tab_summary:
        resume_profile: ResumeParseResult | None = st.session_state.resume_profile
        skills: list[ExtractedSkill] = st.session_state.skills or []
        role_matches: list[RoleMatch] = st.session_state.role_matches or []
        portfolio: PortfolioReport | None = st.session_state.portfolio_report
        interview_prep: InterviewPrepReport | None = st.session_state.interview_prep
        learning_validation: ContinuousLearningReport | None = st.session_state.learning_validation
        career_trajectory: CareerTrajectoryReport | None = st.session_state.career_trajectory
        comprehensive = st.session_state.comprehensive_gap_analysis
        temporal_dynamics = st.session_state.temporal_dynamics
        fairness: FairnessReport | None = st.session_state.fairness

        executive = build_executive_summary(
            resume_profile=resume_profile,
            role_matches=role_matches,
            portfolio_report=portfolio,
            interview_prep=interview_prep,
            learning_validation=learning_validation,
            career_trajectory=career_trajectory,
            comprehensive_analysis=comprehensive,
            temporal_dynamics=temporal_dynamics,
            fairness=fairness,
        )

        st.subheader("Executive Summary")
        st.markdown(
            f"""
            <div class="surface-card">
                <div class="surface-title">Top Recommendation</div>
                <div class="surface-copy">{executive.get("headline", "Run the analysis to generate a summary.")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        top_role = role_matches[0] if role_matches else None
        summary_cols = st.columns(5)
        summary_cols[0].metric("Top Role", top_role.role if top_role else "N/A")
        summary_cols[1].metric("Role Match", f"{top_role.score:.1f}%" if top_role else "N/A")
        summary_cols[2].metric("Skills", len(skills))
        summary_cols[3].metric("Portfolio", f"{portfolio.portfolio_score:.1f}/100" if portfolio else "N/A")
        summary_cols[4].metric("Interview Readiness", f"{interview_prep.success_probability:.0f}%" if interview_prep else "N/A")

        actions = executive.get("actions", [])
        if actions:
            st.markdown("### Recommended Next Actions")
            for action in actions:
                st.markdown(f"- {action}")

        report_markdown = build_markdown_report(
            resume_profile=resume_profile,
            skills_count=len(skills),
            role_matches=role_matches,
            portfolio_report=portfolio,
            interview_prep=interview_prep,
            learning_validation=learning_validation,
            career_trajectory=career_trajectory,
            comprehensive_analysis=comprehensive,
            temporal_dynamics=temporal_dynamics,
            fairness=fairness,
        )
        st.download_button(
            "Download Career Report",
            data=report_markdown,
            file_name="fair_path_career_report.md",
            mime="text/markdown",
        )

    with tab_skills:
        skills: list[ExtractedSkill] = st.session_state.skills
        resume_profile: ResumeParseResult | None = st.session_state.resume_profile
        st.subheader(f"Extracted Skills ({len(skills)})")

        if resume_profile is not None:
            profile_cols = st.columns(3)
            profile_cols[0].metric("Email", resume_profile.email or "Not found")
            profile_cols[1].metric("Phone", resume_profile.phone or "Not found")
            exp_value = (
                f"{resume_profile.experience_years} yrs"
                if resume_profile.experience_years is not None
                else "Not found"
            )
            profile_cols[2].metric("Experience", exp_value)
            st.divider()

        # Group by category
        cat_map: dict[str, list[ExtractedSkill]] = {}
        uncategorised: list[ExtractedSkill] = []
        for sk in skills:
            placed = False
            for cat_name, cat_skills in SKILL_CATEGORIES.items():
                if sk.canonical in cat_skills:
                    cat_map.setdefault(cat_name, []).append(sk)
                    placed = True
                    break
            if not placed:
                uncategorised.append(sk)

        # Summary metrics
        cols = st.columns(5)
        prof_counts = {"expert": 0, "advanced": 0, "intermediate": 0, "basic": 0}
        for s in skills:
            prof_counts[s.proficiency] = prof_counts.get(s.proficiency, 0) + 1
        cols[0].metric("Total Skills", len(skills))
        cols[1].metric("Expert", prof_counts.get("expert", 0))
        cols[2].metric("Advanced", prof_counts.get("advanced", 0))
        cols[3].metric("Intermediate", prof_counts.get("intermediate", 0))
        cols[4].metric("Basic", prof_counts.get("basic", 0))

        # Category cards
        for cat_name in list(cat_map.keys()) + (["Other"] if uncategorised else []):
            cat_skills = cat_map.get(cat_name, uncategorised)
            if not cat_skills:
                continue
            with st.expander(f"**{cat_name}** ({len(cat_skills)})", expanded=True):
                chips_html = ""
                for s in sorted(cat_skills, key=lambda x: x.canonical):
                    chip_class = "chip-advanced"
                    if s.proficiency == "basic":
                        chip_class = "chip-basic"
                    elif s.proficiency == "intermediate":
                        chip_class = "chip-intermediate"
                    chips_html += (
                        f'<span class="skill-chip {chip_class}" title="Section: {s.source_section} | '
                        f'Proficiency: {s.proficiency} | Score: {s.proficiency_score:.2f}">{s.canonical} ({s.proficiency})</span>'
                    )
                st.markdown(chips_html, unsafe_allow_html=True)

        # Tabular detail
        with st.expander("Detailed skill table"):
            df = pd.DataFrame([s.model_dump() for s in skills])
            st.dataframe(df, width="stretch", hide_index=True)
        with st.expander("Proficiency evidence"):
            for skill in sorted(skills, key=lambda item: (-item.proficiency_score, item.canonical)):
                evidence = ", ".join(skill.proficiency_evidence) if skill.proficiency_evidence else "No strong contextual evidence found"
                st.markdown(
                    f"**{skill.canonical}**: {skill.proficiency.title()} ({skill.proficiency_score:.2f})"
                )
                st.caption(evidence)

    with tab_roles:
        role_matches: list[RoleMatch] = st.session_state.role_matches or []
        st.subheader(f"Suitable Job Roles ({len(role_matches)})")

        if not role_matches:
            st.info("No matching roles found. Try lowering the minimum score or uploading a different resume.")
        else:
            # Domain summary
            domains = {}
            for rm in role_matches:
                domains[rm.domain] = domains.get(rm.domain, 0) + 1
            cols = st.columns(min(len(domains), 4))
            for idx, (dom, cnt) in enumerate(sorted(domains.items(), key=lambda x: -x[1])):
                cols[idx % len(cols)].metric(dom, f"{cnt} role{'s' if cnt > 1 else ''}")

            st.divider()

            for i, rm in enumerate(role_matches, 1):
                with st.expander(
                    f"**#{i} - {rm.role}** ({rm.domain}) - Score: {rm.score:.1f}%",
                    expanded=i <= 3,
                ):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Match Score", f"{rm.score:.1f}%")
                    c2.metric("Core Skills Covered", f"{rm.core_match_pct:.0f}%")
                    c3.metric("Total Skills Matched", rm.total_matched)
                    c4.metric("Proficiency Fit", f"{rm.proficiency_alignment:.0f}%")

                    st.caption(rm.description)

                    sk1, sk2 = st.columns(2)
                    with sk1:
                        st.markdown("**Your Matching Skills**")
                        all_matched = rm.matched_core + rm.matched_optional
                        if all_matched:
                            core_html = "".join(
                                f'<span class="skill-chip chip-advanced">{s}</span>' for s in rm.matched_core
                            )
                            opt_html = "".join(
                                f'<span class="skill-chip chip-intermediate">{s}</span>' for s in rm.matched_optional
                            )
                            st.markdown(core_html + opt_html, unsafe_allow_html=True)
                        else:
                            st.caption("None")
                    with sk2:
                        st.markdown("**Skills to Learn**")
                        if rm.missing_core:
                            miss_html = "".join(
                                f'<span class="skill-chip chip-basic">{s}</span>' for s in rm.missing_core
                            )
                            st.markdown(miss_html, unsafe_allow_html=True)
                        else:
                            st.success("You have all core skills!")

                    # Progress bar
                    st.progress(min(rm.score / 100.0, 1.0))

                    role_explanation = (st.session_state.role_explanations or {}).get(rm.role)
                    if role_explanation:
                        st.markdown("**Why This Role Fits? (SHAP)**")
                        st.caption(role_explanation.get("summary", ""))

                        pos_factors = role_explanation.get("positive_factors", [])
                        neg_factors = role_explanation.get("negative_factors", [])
                        reason_left, reason_right = st.columns(2)
                        with reason_left:
                            st.markdown("**Positive Drivers**")
                            if pos_factors:
                                for factor in pos_factors:
                                    st.write(f"+ {factor['label']} ({factor['impact']:+.2f})")
                            else:
                                st.caption("No strong positive drivers found.")
                        with reason_right:
                            st.markdown("**Negative Drivers**")
                            if neg_factors:
                                for factor in neg_factors:
                                    st.write(f"{factor['impact']:+.2f} {factor['label']}")
                            else:
                                st.caption("No strong negative drivers found.")

    with tab_portfolio:
        portfolio: PortfolioReport | None = st.session_state.portfolio_report
        st.subheader("Portfolio Validation")

        if portfolio is None:
            st.info("Run the analysis first to validate resume skills against your portfolio.")
        else:
            st.caption(portfolio.summary)
            top_cols = st.columns(5)
            top_cols[0].metric("Portfolio Score", f"{portfolio.portfolio_score:.1f}/100")
            top_cols[1].metric("Activity", f"{portfolio.activity_score:.1f}/25")
            top_cols[2].metric("Complexity", f"{portfolio.complexity_score:.1f}/25")
            top_cols[3].metric("Documentation", f"{portfolio.documentation_score:.1f}/20")
            top_cols[4].metric("Impact", f"{portfolio.impact_score:.1f}/30")

            if portfolio.profile_url:
                st.markdown(f"Profile: [{portfolio.profile_url}]({portfolio.profile_url})")
            st.caption(f"Source status: {portfolio.source_status}")

            verified_left, verified_right = st.columns(2)
            with verified_left:
                st.markdown("**Verified Skills**")
                if portfolio.verified_skills:
                    for item in portfolio.verified_skills[:8]:
                        st.markdown(f"- **{item.skill}** ({item.confidence:.2f})")
                        if item.evidence:
                            st.caption(", ".join(item.evidence))
                else:
                    st.caption("No verified portfolio-backed skills found yet.")
            with verified_right:
                st.markdown("**Skills Needing Stronger Proof**")
                if portfolio.weak_skills:
                    for item in portfolio.weak_skills[:8]:
                        st.markdown(f"- **{item.skill}** ({item.status})")
                        if item.evidence:
                            st.caption(", ".join(item.evidence))
                else:
                    st.caption("No weak skill claims detected.")

            if portfolio.repositories:
                st.markdown("### Repository Evidence")
                repo_df = pd.DataFrame([repo.model_dump() for repo in portfolio.repositories])
                st.dataframe(repo_df, width="stretch", hide_index=True)
            else:
                st.info("No repository metadata available yet. Add a public GitHub profile or enable API access.")

            if portfolio.recommendations:
                st.markdown("### Recommendations")
                for recommendation in portfolio.recommendations:
                    st.markdown(f"- {recommendation}")

    with tab_interview:
        interview_prep: InterviewPrepReport | None = st.session_state.interview_prep
        st.subheader("Interview Preparation")

        if interview_prep is None:
            st.info("Run the analysis first to generate interview preparation for the target role.")
        else:
            st.caption(interview_prep.summary)
            prep_cols = st.columns(3)
            prep_cols[0].metric("Success Probability", f"{interview_prep.success_probability:.1f}%")
            prep_cols[1].metric("Readiness", interview_prep.readiness_level)
            prep_cols[2].metric("Focus Skills", len(interview_prep.focus_skills))

            if interview_prep.focus_skills:
                st.markdown("### Focus Areas")
                st.markdown(", ".join(f"`{skill}`" for skill in interview_prep.focus_skills))

            if interview_prep.recommendations:
                st.markdown("### Recommendations")
                for recommendation in interview_prep.recommendations:
                    st.markdown(f"- {recommendation}")

            st.markdown("### Question Bank")
            questions = interview_prep.questions
            for index, question in enumerate(questions[:12], 1):
                with st.expander(f"Q{index}. {question.skill.title()} - {question.category.title()} ({question.difficulty})", expanded=index <= 4):
                    st.write(question.question)
                    if question.expected_points:
                        st.caption("Expected points: " + ", ".join(question.expected_points))

            if questions:
                st.markdown("### Mock Answer Practice")
                question_labels = [
                    f"{item.skill.title()} | {item.category.title()} | {item.question}"
                    for item in questions[:8]
                ]
                selected_label = st.selectbox("Choose a question", question_labels, key="interview_question_choice")
                selected_index = question_labels.index(selected_label)
                selected_question = questions[selected_index]
                practice_answer = st.text_area(
                    "Write your answer",
                    height=180,
                    key="interview_mock_answer",
                    placeholder="Explain your answer with concepts, steps, tradeoffs, and one concrete example.",
                )
                if st.button("Evaluate Practice Answer", key="evaluate_mock_answer_btn"):
                    evaluation = evaluate_mock_answer(selected_question, practice_answer)
                    eval_cols = st.columns(4)
                    eval_cols[0].metric("Correctness", f"{evaluation.correctness:.0f}%")
                    eval_cols[1].metric("Completeness", f"{evaluation.completeness:.0f}%")
                    eval_cols[2].metric("Clarity", f"{evaluation.clarity:.0f}%")
                    eval_cols[3].metric("Overall", f"{evaluation.overall:.0f}%")
                    st.markdown("**Feedback**")
                    st.write(evaluation.feedback)
                    if evaluation.missing_points:
                        st.markdown("**Missing Points**")
                        for point in evaluation.missing_points:
                            st.markdown(f"- {point}")

    # ── TAB: Skill Gaps ───────────────────────────────────────────────
    with tab_validate:
        learning_validation: ContinuousLearningReport | None = st.session_state.learning_validation
        st.subheader("Continuous Learning Validator")

        if learning_validation is None:
            st.info("Run the analysis first to generate learning checkpoints from the roadmap.")
        else:
            st.caption(learning_validation.summary)
            validate_cols = st.columns(3)
            validate_cols[0].metric("Checkpoints", len(learning_validation.checkpoints))
            validate_cols[1].metric("Focus Skills", len(learning_validation.focus_skills))
            validate_cols[2].metric("Target Role", learning_validation.target_role)

            if learning_validation.recommendations:
                st.markdown("### Validator Strategy")
                for item in learning_validation.recommendations:
                    st.markdown(f"- {item}")

            if learning_validation.checkpoints:
                st.markdown("### Roadmap Checkpoints")
                for checkpoint in learning_validation.checkpoints[:6]:
                    with st.expander(
                        f"{checkpoint.skill.title()} - {checkpoint.milestone_label} "
                        f"(Target {checkpoint.target_score:.0f}%)",
                        expanded=checkpoint == learning_validation.checkpoints[0],
                    ):
                        info_cols = st.columns(4)
                        info_cols[0].metric("Target Weeks", checkpoint.target_weeks)
                        info_cols[1].metric("Target Score", f"{checkpoint.target_score:.0f}%")
                        info_cols[2].metric("Estimated Hours", checkpoint.estimated_hours)
                        info_cols[3].metric("Questions", len(checkpoint.questions))

                        if checkpoint.assessment_focus:
                            st.markdown("**Assessment Focus**")
                            st.markdown(", ".join(f"`{item}`" for item in checkpoint.assessment_focus))

                        if checkpoint.practice_evidence:
                            st.markdown("**Practice Evidence Expected**")
                            for item in checkpoint.practice_evidence:
                                st.markdown(f"- {item}")

                st.markdown("### Validate One Skill")
                checkpoint_labels = [
                    f"{item.skill.title()} | {item.milestone_label} | Target {item.target_score:.0f}%"
                    for item in learning_validation.checkpoints
                ]
                selected_checkpoint_label = st.selectbox(
                    "Choose a checkpoint",
                    checkpoint_labels,
                    key="learning_validator_checkpoint_choice",
                )
                selected_checkpoint = learning_validation.checkpoints[
                    checkpoint_labels.index(selected_checkpoint_label)
                ]

                answers: list[str] = []
                for idx, question in enumerate(selected_checkpoint.questions, 1):
                    st.markdown(f"**Question {idx}**")
                    st.write(question.prompt)
                    answers.append(
                        st.text_area(
                            f"Answer {idx}",
                            key=f"learning_validator_answer_{selected_checkpoint.skill}_{idx}",
                            height=110,
                            placeholder="Write a short but concrete answer with concepts, steps, and one example.",
                        )
                    )

                evidence_text = st.text_area(
                    "Project or practice evidence",
                    key=f"learning_validator_evidence_{selected_checkpoint.skill}",
                    height=120,
                    placeholder="Describe what you built, what worked, what failed, and what proof you have.",
                )

                if st.button("Evaluate Learning Checkpoint", key="evaluate_learning_checkpoint_btn"):
                    result = evaluate_learning_checkpoint(
                        selected_checkpoint,
                        answers=answers,
                        evidence_text=evidence_text,
                    )
                    result_cols = st.columns(4)
                    result_cols[0].metric("Theory", f"{result.theory_score:.0f}%")
                    result_cols[1].metric("Practical", f"{result.practical_score:.0f}%")
                    result_cols[2].metric("Overall", f"{result.overall_score:.0f}%")
                    result_cols[3].metric("Status", result.readiness_level)

                    st.markdown("**Feedback**")
                    st.write(result.feedback)

                    if result.strengths:
                        st.markdown("**Strengths**")
                        for item in result.strengths:
                            st.markdown(f"- {item}")

                    if result.missing_points:
                        st.markdown("**Missing Points**")
                        for item in result.missing_points:
                            st.markdown(f"- {item}")

                    if result.next_actions:
                        st.markdown("**Next Actions**")
                        for item in result.next_actions:
                            st.markdown(f"- {item}")

    with tab_career:
        career_trajectory: CareerTrajectoryReport | None = st.session_state.career_trajectory
        st.subheader("Career Trajectory Simulation")

        if career_trajectory is None or not career_trajectory.paths:
            st.info("Run the analysis first to simulate future career paths from your top role matches.")
        else:
            st.caption(career_trajectory.summary)
            top_path = career_trajectory.paths[0]
            overview_cols = st.columns(4)
            overview_cols[0].metric("Recommended Path", career_trajectory.recommended_path)
            overview_cols[1].metric("5-Year Salary", f"{top_path.salary_year_5_lpa:.1f} LPA")
            overview_cols[2].metric("Success Probability", f"{top_path.success_probability:.0f}%")
            overview_cols[3].metric("ROI Score", f"{top_path.roi_score:.0f}/100")

            st.markdown("### Path Comparison")
            comparison_df = pd.DataFrame(
                [
                    {
                        "Role": path.role,
                        "Domain": path.domain,
                        "Current Match %": round(path.current_match_score, 1),
                        "Projected Match %": round(path.projected_match_after_learning, 1),
                        "Year 1 LPA": round(path.salary_year_1_lpa, 1),
                        "Year 3 LPA": round(path.salary_year_3_lpa, 1),
                        "Year 5 LPA": round(path.salary_year_5_lpa, 1),
                        "Growth %": round(path.growth_rate_pct, 1),
                        "Success %": round(path.success_probability, 1),
                        "Risk": path.risk_level,
                        "ROI": round(path.roi_score, 1),
                    }
                    for path in career_trajectory.paths
                ]
            )
            st.dataframe(comparison_df, width="stretch", hide_index=True)

            st.markdown("### Detailed Path Outlook")
            for index, path in enumerate(career_trajectory.paths, 1):
                with st.expander(
                    f"#{index} {path.role} - ROI {path.roi_score:.0f}/100 - 5Y {path.salary_year_5_lpa:.1f} LPA",
                    expanded=index == 1,
                ):
                    path_cols = st.columns(5)
                    path_cols[0].metric("Current Match", f"{path.current_match_score:.0f}%")
                    path_cols[1].metric("After Learning", f"{path.projected_match_after_learning:.0f}%")
                    path_cols[2].metric("Year 1", f"{path.salary_year_1_lpa:.1f} LPA")
                    path_cols[3].metric("Year 3", f"{path.salary_year_3_lpa:.1f} LPA")
                    path_cols[4].metric("Year 5", f"{path.salary_year_5_lpa:.1f} LPA")

                    risk_cols = st.columns(3)
                    risk_cols[0].metric("Growth Rate", f"{path.growth_rate_pct:.1f}%")
                    risk_cols[1].metric("Success Probability", f"{path.success_probability:.0f}%")
                    risk_cols[2].metric("Risk", path.risk_level)

                    if path.top_missing_skills:
                        st.markdown("**Skills That Decide This Path**")
                        st.markdown(", ".join(f"`{skill}`" for skill in path.top_missing_skills))

                    st.markdown("**Recommendation**")
                    st.write(path.recommendation)

    with tab_gaps:
        st.subheader("Skill Gap Analysis")
        
        # Use comprehensive gap analysis if available
        comprehensive = st.session_state.comprehensive_gap_analysis
        gaps: list[SkillGap] = st.session_state.gaps or []

        # Debug: Show what we have
        if st.checkbox("Show analysis debug info"):
            st.write(f"Comprehensive analysis available: {comprehensive is not None}")
            st.write(f"Basic gaps available: {len(gaps) > 0}")
            st.write(f"HAS_GAP_ANALYSIS: {HAS_GAP_ANALYSIS}")
            if comprehensive:
                st.write(f"Comprehensive keys: {list(comprehensive.keys())}")

        if comprehensive and comprehensive.get('ranked_priorities'):
            # ─── COMPREHENSIVE GAP ANALYSIS ────────────────────
            st.success("Advanced Gap Analysis - AI-powered comprehensive skill gap evaluation")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            gaps_by_cat = comprehensive.get('gaps_by_category', {})
            ranked_priorities = comprehensive.get('ranked_priorities', [])
            learning_path = comprehensive.get('learning_path', {})
            skill_graph = comprehensive.get('skill_graph', {})
            
            with col1:
                total_gaps = (len(gaps_by_cat.get('critical', [])) + 
                             len(gaps_by_cat.get('important', [])) + 
                             len(gaps_by_cat.get('nice_to_have', [])))
                st.metric("Total Gaps", total_gaps)
            
            with col2:
                st.metric("Critical", len(gaps_by_cat.get('critical', [])))
            
            with col3:
                st.metric("Important", len(gaps_by_cat.get('important', [])))
            
            with col4:
                st.metric("Nice-to-have", len(gaps_by_cat.get('nice_to_have', [])))
            
            # Tabs for different gap analysis views
            gap_tab1, gap_tab2, gap_tab3, gap_tab4, gap_tab5 = st.tabs(
                ["Priority Ranking", "Learning Path", "Skill Graph", "Quick Wins", "Breakdown"]
            )
            
            # ─── TAB 1: PRIORITY RANKING ─────────────────────
            with gap_tab1:
                st.markdown("### Ranked Skills by Priority")
                
                if ranked_priorities:
                    # Top priority skills
                    for idx, skill_data in enumerate(ranked_priorities[:10], 1):
                        skill = skill_data.get('skill', 'Unknown')
                        priority = skill_data.get('priority_score', 0)
                        tier = skill_data.get('rank_tier', 'LOW')
                        breakdown = skill_data.get('breakdown', {})
                        
                        # Safe conversion to int with fallback
                        try:
                            learning_time = int(skill_data.get('learning_time_months', 0) or 0)
                        except (ValueError, TypeError):
                            learning_time = 0
                        
                        try:
                            salary_boost = int(skill_data.get('salary_boost_inr', 0) or 0)
                        except (ValueError, TypeError):
                            salary_boost = 0
                        
                        category = skill_data.get('category', 'OTHER')
                        
                        # Color coding for tier
                        tier_label = {
                            'CRITICAL': 'Critical',
                            'HIGH': 'High',
                            'MEDIUM': 'Medium',
                            'LOW': 'Low',
                        }.get(tier, 'Other')
                        
                        with st.expander(
                            f"**#{idx} - {skill.title()}** "
                            f"(Score: {priority:.1f}/100 - {category})",
                            expanded=idx <= 3
                        ):
                            col_score, col_learn, col_salary = st.columns(3)
                            
                            with col_score:
                                st.metric(f"Priority Score", f"{priority:.1f}", 
                                         delta=f"{tier}")
                                # Score breakdown
                                st.caption("**Score Breakdown:**")
                                for factor, value in breakdown.items():
                                    st.text(f"  {factor.replace('_', ' ').title()}: {value:.0f}")
                            
                            with col_learn:
                                st.metric("Time to Learn", f"{learning_time} months")
                                # Time gauge
                                ease_score = breakdown.get('learning_ease', 50)
                                st.progress(min(ease_score / 100, 1.0))
                                st.caption(f"*Difficulty: {100 - ease_score:.0f}%*")
                            
                            with col_salary:
                                if salary_boost > 0:
                                    st.metric("Salary Boost", f"₹{salary_boost:,.0f}")
                                    st.success(f"+{(salary_boost/100000):.1f}L potential")
                                else:
                                    st.metric("Salary Boost", "N/A")
                            
                            # Recommendation
                            recommendation = skill_data.get('recommendation', '')
                            if recommendation:
                                st.markdown(f"**Recommendation:**\n{recommendation}")
                else:
                    st.success("No gaps identified or all high-priority skills are already present.")
            
            # ─── TAB 2: LEARNING PATH ────────────────────────
            with gap_tab2:
                st.markdown("### Month-by-Month Learning Timeline")
                
                if learning_path:
                    # Check if this is LLM-generated (new structure) or rule-based (old structure)
                    is_llm_path = isinstance(learning_path, dict) and 'learning_path' in learning_path
                    
                    if is_llm_path:
                        # LLM-GENERATED LEARNING PATH
                        path_data = learning_path.get('learning_path', {})
                        
                        # Summary metrics
                        initial_score = comprehensive.get('current_match_score', 0) if comprehensive else 0
                        target_score = path_data.get('final_match_score', 90)
                        total_duration = path_data.get('total_months', 6)
                        total_hours = path_data.get('estimated_hours_total', 'N/A')
                        
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Current Score", f"{initial_score:.0f}%")
                        col2.metric("Target Score", f"{target_score:.0f}%", delta=f"+{target_score - initial_score:.0f}%")
                        col3.metric("Duration", f"{total_duration} months")
                        col4.metric("Total Hours", f"~{total_hours}")
                        
                        st.divider()
                        render_learning_path(path_data, initial_score=float(initial_score))
                        st.divider()

                        # Display milestones
                        milestones = path_data.get('milestones', [])
                        if milestones:
                            st.markdown("#### Month-by-Month Milestones")
                            
                            for idx, milestone in enumerate(milestones, 1):
                                month_start = milestone.get('month_start', idx)
                                month_end = milestone.get('month_end', month_start)
                                month_label = (
                                    f"Month {month_start}"
                                    if month_start == month_end
                                    else f"Months {month_start}-{month_end}"
                                )
                                with st.expander(
                                    f"{month_label}: {milestone.get('skill', 'Unknown')} "
<<<<<<< HEAD
                                    f"({milestone.get('category', 'N/A')}) -> {milestone.get('match_score_after', 0):.0f}%",
=======
                                    f"({milestone.get('category', 'N/A')}) → {milestone.get('match_score_after', 0):.0f}%",
>>>>>>> 762d549ff5cab1fc93bc6825be5008a3d4e0034c
                                    expanded=(idx <= 2)
                                ):
                                    # Milestone details
                                    col_left, col_right = st.columns([2, 1])
                                    
                                    with col_left:
                                        st.caption(f"**Week:** {milestone.get('week_range', 'N/A')}")
                                        st.caption(f"**Time Commitment:** {milestone.get('estimated_hours_per_week', 8)} hours/week")
                                        st.caption(f"**Difficulty:** {milestone.get('difficulty', 'moderate')}")
                                        
                                        # Learning objectives
                                        objectives = milestone.get('learning_objectives', [])
                                        if objectives:
                                            st.write("**Learning Objectives:**")
                                            for obj in objectives:
                                                st.write(f"- {obj}")
                                        
                                        # Resources
                                        resources = milestone.get('resources', [])
                                        if resources:
                                            st.write("**Recommended Resources:**")
                                            for resource in resources:
                                                res_name = resource.get('name', 'Resource')
                                                res_type = resource.get('type', 'resource')
                                                res_cost = resource.get('cost', 'N/A')
                                                res_platform = resource.get('platform', 'Online')
                                                st.write(f"- **{res_name}** ({res_platform}) - {res_cost}")
                                        
                                        # Practice projects
                                        projects = milestone.get('practice_projects', [])
                                        if projects:
                                            st.write("**Practice Projects:**")
                                            for project in projects:
                                                st.write(f"- {project}")
                                        
                                        # Success criteria
                                        criteria = milestone.get('success_criteria', [])
                                        if criteria:
                                            st.write("**Success Criteria:**")
                                            for criterion in criteria:
                                                st.write(f"- {criterion}")
                                    
                                    with col_right:
                                        # Score progress
                                        score_after = milestone.get('match_score_after', 0)
                                        score_improvement = milestone.get('score_improvement', 0)
                                        st.metric(
                                            "Match After",
                                            f"{score_after:.0f}%",
                                            delta=f"+{score_improvement:.0f}%"
                                        )
                        
                        # Quick wins section
                        quick_wins = path_data.get('quick_wins', [])
                        if quick_wins:
                            st.divider()
                            st.markdown("#### Quick Wins")
                            for qw in quick_wins:
                                st.success(
                                    f"**{qw.get('skill', 'Skill')}**: {qw.get('why_quick_win', 'High impact')} | "
                                    f"Time: {qw.get('time_needed', 'N/A')}"
                                )
                        
                        # Recommendations
                        recommendations = path_data.get('key_recommendations', [])
                        if recommendations:
                            st.divider()
                            st.markdown("#### Key Recommendations")
                            for rec in recommendations:
                                st.write(f"- {rec}")
                        
                        # Show powered by
                        st.divider()
                        st.caption("Powered by Groq - Personalized learning path")
                    
                    elif learning_path and learning_path.get('milestones'):
                        # RULE-BASED LEARNING PATH (Enhanced with detailed information)
                        initial_score = learning_path.get('initial_match_score', 0)
                        final_score = learning_path.get('final_match_score', initial_score)
                        total_improvement = learning_path.get('total_improvement', 0)
                        total_duration = learning_path.get('total_duration_months', 0)
                        milestones = learning_path.get('milestones', [])
                        
                        # Summary
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Starting Score", f"{initial_score:.0f}%")
                        col2.metric("Projected Score", f"{final_score:.0f}%", delta=f"+{total_improvement:.0f}%")
                        col3.metric("Duration", f"{total_duration:.0f} months")
                        col4.metric("Skills to Learn", len([m for m in milestones if m.get('type') == 'priority']))
                        
                        st.divider()
                        st.markdown("#### Month-by-Month Milestones")
                        
                        # Display milestones with expandable details
                        for idx, milestone in enumerate(milestones[:12], 1):
                            skill_name = milestone.get('skill', 'Unknown')
                            category = milestone.get('category', 'IMPORTANT')
                            duration = milestone.get('duration_months', 0)
                            score_after = milestone.get('match_score_after', 0)
                            difficulty = milestone.get('difficulty', 'moderate')
                            
                            # Color code by category
                            category_label = {
                                'CRITICAL': 'Critical',
                                'IMPORTANT': 'Important',
                                'NICE_TO_HAVE': 'Nice-to-have'
                            }.get(category, 'Other')
                            
                            with st.expander(
                                f"Month {milestone.get('month', idx)}: {skill_name.title()} {category_label} "
                                f"({category}) -> {score_after:.0f}%",
                                expanded=(idx <= 2)
                            ):
                                col_left, col_right = st.columns([2, 1])
                                
                                with col_left:
                                    st.caption(f"**Week:** {milestone.get('week_range', 'N/A')}")
                                    st.caption(f"**Time Commitment:** {milestone.get('estimated_hours_per_week', 8)} hours/week")
                                    st.caption(f"**Duration:** {duration} months")
                                    st.caption(f"**Difficulty:** {difficulty.title()}")
                                    
                                    # Learning objectives
                                    objectives = milestone.get('learning_objectives', [])
                                    if objectives:
                                        st.write("**Learning Objectives:**")
                                        for obj in objectives:
                                            st.write(f"- {obj}")
                                    
                                    # Resources
                                    resources = milestone.get('resources', [])
                                    if resources:
                                        st.write("**Recommended Resources:**")
                                        for resource in resources:
                                            res_name = resource.get('name', 'Resource') if isinstance(resource, dict) else resource
                                            res_type = resource.get('type', 'resource').title() if isinstance(resource, dict) else 'Resource'
                                            res_platform = resource.get('platform', 'Online') if isinstance(resource, dict) else 'Online'
                                            res_cost = resource.get('cost', 'varies') if isinstance(resource, dict) else 'varies'
                                            st.write(f"- **{res_name}** ({res_platform}) - {res_cost}")
                                    
                                    # Practice projects
                                    projects = milestone.get('practice_projects', [])
                                    if projects:
                                        st.write("**Practice Projects:**")
                                        for project in projects:
                                            st.write(f"- {project}")
                                    
                                    # Success criteria
                                    criteria = milestone.get('success_criteria', [])
                                    if criteria:
                                        st.write("**Success Criteria:**")
                                        for criterion in criteria:
                                            st.write(f"- {criterion}")
                                
                                with col_right:
                                    score_improvement = milestone.get('score_improvement', 0)
                                    st.metric(
                                        "Match After",
                                        f"{score_after:.0f}%",
                                        delta=f"+{score_improvement:.0f}%" if score_improvement > 0 else None
                                    )
                else:
                    st.info("Learning path will be generated once gaps are identified.")

                if False and skill_graph:
                    st.divider()
                    st.markdown("### Skill Dependency Graph")
                    st.markdown(
                        f"""
                        <div class="surface-card">
                            <div class="surface-title">Dependency Insight</div>
                            <div class="surface-copy">{skill_graph.get('summary', 'No graph insight available yet.')}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    graph_col1, graph_col2 = st.columns(2)
                    with graph_col1:
                        st.markdown("**Top Bottlenecks**")
                        bottlenecks = skill_graph.get("bottlenecks", [])
                        if bottlenecks:
                            for item in bottlenecks[:4]:
                                unlocks = ", ".join(item.get("unlocks", [])[:4]) or "downstream skills"
                                st.markdown(
                                    f"- **{item.get('skill', 'unknown')}** unlocks {item.get('unlock_count', 0)} areas: {unlocks}"
                                )
                        else:
                            st.caption("No major bottlenecks detected.")

                        st.markdown("**Critical Paths**")
                        critical_paths = skill_graph.get("critical_path", [])
                        if critical_paths:
                            for item in critical_paths:
                                path_text = " -> ".join(item.get("path", []))
                                st.markdown(f"- **{item.get('skill', 'unknown')}**: {path_text}")
                        else:
                            st.caption("No long dependency path detected.")

                    with graph_col2:
                        st.markdown("**Transferable Skills**")
                        substitutes = skill_graph.get("substitute_matches", [])
                        if substitutes:
                            for item in substitutes[:4]:
                                st.markdown(
                                    f"- **{item.get('source_skill', 'unknown')}** can accelerate **{item.get('target_skill', 'unknown')}** "
                                    f"({int(float(item.get('transferability', 0.0)) * 100)}% transferable)"
                                )
                                st.caption(item.get("recommendation", ""))
                        else:
                            st.caption("No strong substitute skill path detected.")

                        graph_skills = skill_graph.get("graph_skills", [])
                        if graph_skills:
                            st.markdown("**Graph Skills**")
                            st.markdown(", ".join(f"`{skill}`" for skill in graph_skills[:12]))

                    mermaid_code = skill_graph.get("mermaid", "")
                    if mermaid_code:
                        st.markdown("**Dependency Map**")
                        _render_mermaid_diagram(mermaid_code)
                        with st.expander("Dependency map code"):
                            st.code(mermaid_code, language="mermaid")
            
            # ─── TAB 3: SKILL GRAPH ──────────────────────────────
            with gap_tab3:
                st.markdown("### Skill Dependency Graph")
                if skill_graph:
                    st.markdown(
                        f"""
                        <div class="surface-card">
                            <div class="surface-title">Dependency Insight</div>
                            <div class="surface-copy">{skill_graph.get('summary', 'No graph insight available yet.')}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    graph_col1, graph_col2 = st.columns(2)
                    with graph_col1:
                        st.markdown("**Top Bottlenecks**")
                        bottlenecks = skill_graph.get("bottlenecks", [])
                        if bottlenecks:
                            for item in bottlenecks[:4]:
                                unlocks = ", ".join(item.get("unlocks", [])[:4]) or "downstream skills"
                                st.markdown(
                                    f"- **{item.get('skill', 'unknown')}** unlocks {item.get('unlock_count', 0)} areas: {unlocks}"
                                )
                        else:
                            st.caption("No major bottlenecks detected.")

                        st.markdown("**Critical Paths**")
                        critical_paths = skill_graph.get("critical_path", [])
                        if critical_paths:
                            for item in critical_paths:
                                path_text = " -> ".join(item.get("path", []))
                                st.markdown(f"- **{item.get('skill', 'unknown')}**: {path_text}")
                        else:
                            st.caption("No long dependency path detected.")

                    with graph_col2:
                        st.markdown("**Transferable Skills**")
                        substitutes = skill_graph.get("substitute_matches", [])
                        if substitutes:
                            for item in substitutes[:4]:
                                st.markdown(
                                    f"- **{item.get('source_skill', 'unknown')}** can accelerate **{item.get('target_skill', 'unknown')}** "
                                    f"({int(float(item.get('transferability', 0.0)) * 100)}% transferable)"
                                )
                                st.caption(item.get("recommendation", ""))
                        else:
                            st.caption("No strong substitute skill path detected.")

                        graph_skills = skill_graph.get("graph_skills", [])
                        if graph_skills:
                            st.markdown("**Graph Skills**")
                            st.markdown(", ".join(f"`{skill}`" for skill in graph_skills[:12]))

                    mermaid_code = skill_graph.get("mermaid", "")
                    if mermaid_code:
                        with st.expander("Dependency map code"):
                            st.code(mermaid_code, language="mermaid")
                else:
                    st.info("Skill graph insights will appear after a successful gap analysis.")

            # ─── TAB 4: QUICK WINS ───────────────────────────────
            with gap_tab4:
                st.markdown("### Quick Wins - Learn Fast, High Impact")
                
                quick_wins = comprehensive.get('quick_wins', [])
                
                if quick_wins:
                    cols_per_row = 3
                    for idx in range(0, len(quick_wins), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for col_idx, skill_data in enumerate(quick_wins[idx:idx+cols_per_row]):
                            with cols[col_idx]:
                                skill = skill_data.get('skill', 'Unknown')
                                priority = skill_data.get('priority_score', 0)
                                learning_time = skill_data.get('learning_time_months', 0)
                                ease = skill_data.get('learning_ease', 50)
                                
                                st.markdown(
                                    f"""
                                    **{skill.title()}**
                                    
                                    • Priority: {priority:.0f}/100
                                    • Learn in: {learning_time} months
                                    • Difficulty: {"Easy" if ease > 80 else "Moderate"}
                                    
                                    High ROI - Learn quickly.
                                    """
                                )
                else:
                    st.success("No quick wins needed. You are already on track.")
            
            # ─── TAB 5: BREAKDOWN ────────────────────────────────
            with gap_tab5:
                st.markdown("### Gaps by Category")
                
                # Category summary
                critical = gaps_by_cat.get('critical', [])
                important = gaps_by_cat.get('important', [])
                nice = gaps_by_cat.get('nice_to_have', [])
                
                # Donut chart data
                category_counts = [len(critical), len(important), len(nice)]
                category_labels = ['Critical', 'Important', 'Nice-to-have']
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    chart_data = pd.DataFrame({
                        'Category': category_labels,
                        'Count': category_counts
                    })
                    st.bar_chart(chart_data.set_index('Category'), width="stretch")
                
                with col2:
                    for label, count in zip(category_labels, category_counts):
                        st.metric(label, count)
                
                # Detailed list
                for label, skills in [
                    ('CRITICAL', critical),
                    ('IMPORTANT', important),
                    ('NICE-TO-HAVE', nice),
                ]:
                    if skills:
                        st.markdown(f"### {label}")
                        cols = st.columns(3)
                        for idx, skill in enumerate(skills):
                            cols[idx % 3].markdown(f"- {skill.title()}")

        else:
            # Fallback to basic analysis
            st.info("Basic Gap Analysis - Standard skill gap evaluation")
            
            # Summary counts
            high = sum(1 for g in gaps if g.priority == "High")
            med = sum(1 for g in gaps if g.priority == "Medium")
            low = sum(1 for g in gaps if g.priority == "Low")
            c1, c2, c3 = st.columns(3)
            c1.metric("High Priority", high)
            c2.metric("Medium Priority", med)
            c3.metric("Low Priority", low)

            # Priority cards
            for priority in ["High", "Medium", "Low"]:
                p_gaps = [g for g in gaps if g.priority == priority]
                if not p_gaps:
                    continue
                st.markdown(f"### {priority} Priority")
                for g in p_gaps:
                    pct_bar = min(g.demand_pct, 100)
                    st.markdown(
                        f'<div class="metric-card">'
                        f"<strong>{g.skill}</strong> — "
                        f"Found in **{g.job_count}** jobs ({g.demand_pct:.1f}% of postings)"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

            # Chart
            st.markdown("### Demand Distribution")
            gap_df = pd.DataFrame([g.model_dump() for g in gaps])
            st.bar_chart(gap_df, x="skill", y="demand_pct", color="priority")

    # ── TAB: Trends ────────────────────────────────────────────────────
    with tab_trends:
        trends: list[SkillTrend] = st.session_state.trends or []
        temporal_dynamics = st.session_state.temporal_dynamics
        st.subheader("Market Skill Trends")

        if not trends:
            st.info("No trend data available. Ensure job data exists in the processed directory.")
        else:
            relevant_skills: list[str] = []
            top_roles: list[RoleMatch] = st.session_state.role_matches or []
            if top_roles:
                for role_match in top_roles[:3]:
                    relevant_skills.extend(role_match.missing_core)
            if not relevant_skills:
                gaps: list[SkillGap] = st.session_state.gaps or []
                relevant_skills.extend(gap.skill for gap in gaps[:10])

            if _jobs_df is not None and relevant_skills:
                relevant_trends = get_trends_for_skills(_jobs_df, relevant_skills)
            else:
                trend_lookup = {trend.skill.lower(): trend for trend in trends}
                relevant_trends = [
                    trend_lookup[skill.lower()]
                    for skill in dict.fromkeys(relevant_skills)
                    if skill.lower() in trend_lookup
                ]

            if relevant_trends:
                st.markdown("### Trends For Your Missing Skills")
                rel_cols = st.columns(min(3, len(relevant_trends)))
                for index, trend in enumerate(relevant_trends[:6]):
                    delta = f"{trend.growth_pct:+.1f}%"
                    rel_cols[index % len(rel_cols)].metric(
                        trend.skill,
                        trend.forecast_demand,
                        delta=delta,
                    )
                st.divider()

            if temporal_dynamics is not None:
                st.markdown("### Role Evolution Forecast")
                st.markdown(
                    f"""
                    <div class="surface-card">
                        <div class="surface-title">Requirement Drift for {temporal_dynamics.role}</div>
                        <div class="surface-copy">{temporal_dynamics.summary}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                forecast_cols = st.columns(4)
                forecast_cols[0].metric("Relevant Jobs Sample", temporal_dynamics.jobs_considered)
                forecast_cols[1].metric("Months Covered", temporal_dynamics.months_covered)
                forecast_cols[2].metric(
                    "Projected Match (6m)",
                    f"{temporal_dynamics.projected_match_score_6m:.1f}%",
                    delta=f"{temporal_dynamics.risk_delta_6m:+.1f}%",
                )
                delta_12m = temporal_dynamics.projected_match_score_12m - temporal_dynamics.projected_match_score_6m
                forecast_cols[3].metric(
                    "Projected Match (12m)",
                    f"{temporal_dynamics.projected_match_score_12m:.1f}%",
                    delta=f"{delta_12m:+.1f}%",
                )

                if temporal_dynamics.recommendations:
                    st.markdown("**What to do now**")
                    for recommendation in temporal_dynamics.recommendations:
                        st.markdown(f"- {recommendation}")

                if temporal_dynamics.evolving_skills:
                    st.markdown("### Skills Becoming More Important")
                    evolving_rows = [
                        {
                            "Skill": signal.skill,
                            "Type": signal.skill_type.title(),
                            "Prior %": round(signal.prior_pct, 1),
                            "Current %": round(signal.current_pct, 1),
                            "Projected %": round(signal.projected_pct, 1),
                            "Growth %": round(signal.growth_pct, 1),
                            "Momentum": signal.momentum.replace("-", " ").title(),
                            "Status": signal.requirement_status.replace("-", " ").title(),
                            "Urgency": signal.urgency.replace("-", " ").title(),
                        }
                        for signal in temporal_dynamics.evolving_skills[:10]
                    ]
                    st.dataframe(pd.DataFrame(evolving_rows), width="stretch", hide_index=True)

                    pressure_cols = st.columns(2)
                    with pressure_cols[0]:
                        st.markdown("**Rising Toward Required**")
                        if temporal_dynamics.rising_requirements:
                            for skill in temporal_dynamics.rising_requirements[:6]:
                                st.markdown(f"- {skill.title()}")
                        else:
                            st.caption("No optional skills are clearly moving toward required yet.")
                    with pressure_cols[1]:
                        st.markdown("**Softening or Declining**")
                        if temporal_dynamics.declining_requirements:
                            for skill in temporal_dynamics.declining_requirements[:6]:
                                st.markdown(f"- {skill.title()}")
                        else:
                            st.caption("No meaningful decline signal detected for this role right now.")

                st.divider()

            # Top growing
            growing = sorted(trends, key=lambda t: -t.growth_pct)[:10]
            declining = sorted(trends, key=lambda t: t.growth_pct)[:5]

            col_up, col_down = st.columns(2)
            with col_up:
                st.markdown("### Fastest Growing")
                for t in growing:
                    delta = f"+{t.growth_pct:.1f}%" if t.growth_pct > 0 else f"{t.growth_pct:.1f}%"
                    st.metric(t.skill, f"{t.current_pct:.1f}%", delta=delta)

            with col_down:
                st.markdown("### Declining")
                for t in declining:
                    if t.growth_pct >= 0:
                        continue
                    st.metric(t.skill, f"{t.current_pct:.1f}%", delta=f"{t.growth_pct:.1f}%")

            # Full table
            st.markdown("### Full Trend Table")
            trend_df = pd.DataFrame([t.model_dump() for t in trends])
            st.dataframe(trend_df, width="stretch", hide_index=True)

            # Demand chart
            top_demand = sorted(trends, key=lambda t: -t.current_count)[:20]
            demand_df = pd.DataFrame(
                {"Skill": [t.skill for t in top_demand], "Jobs": [t.current_count for t in top_demand]}
            )
            st.markdown("### Top Skills by Current Demand")
            st.bar_chart(demand_df, x="Skill", y="Jobs")

    # ── TAB: Fairness ──────────────────────────────────────────────────
    with tab_fair:
        fairness: FairnessReport = st.session_state.fairness
        st.subheader("Fairness & Bias Analysis")

        if fairness is None:
            st.info("Run the analysis first.")
        else:
            # Score gauge
            score = fairness.score
            if score >= 80:
                score_label = "Good"
            elif score >= 50:
                score_label = "Moderate Concerns"
            else:
                score_label = "Significant Bias Detected"

            st.markdown(
                f"### Fairness Score: **{score:.0f} / 100** - {score_label}"
            )
            st.progress(score / 100)

            # Category indicators
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Gender Bias", fairness.gender_bias)
            c2.metric("Age Bias", fairness.age_bias)
            c3.metric("Education Bias", fairness.education_bias)
            c4.metric("Experience Bias", fairness.experience_bias)

            extra_cols = st.columns(2)
            extra_cols[0].metric("Mitigated Score", f"{fairness.mitigated_score:.1f}")
            extra_cols[1].metric("DPD", f"{fairness.demographic_parity_difference:.3f}")

            if fairness.variant_scores:
                st.markdown("### Synthetic Variant Sensitivity")
                variant_df = pd.DataFrame(
                    [
                        {"variant": variant_name, "score": score}
                        for variant_name, score in fairness.variant_scores.items()
                    ]
                )
                st.dataframe(variant_df, width="stretch", hide_index=True)

            if fairness.anonymized_text_preview:
                with st.expander("Anonymized Resume Preview"):
                    st.text_area(
                        "Preview",
                        fairness.anonymized_text_preview,
                        height=180,
                        disabled=True,
                    )

            # Per-word SHAP bars
            if fairness.indicators:
                st.markdown("### Per-Word Bias Contributions")
                ind_df = pd.DataFrame([i.model_dump() for i in fairness.indicators])
                st.bar_chart(ind_df, x="word", y="penalty", color="category")

                with st.expander("Detailed indicator table"):
                    st.dataframe(ind_df, width="stretch", hide_index=True)

            # Recommendations
            if fairness.recommendations:
                st.markdown("### Recommendations")
                for rec in fairness.recommendations:
                    st.markdown(f"- {rec}")
            else:
                st.success("No bias-related recommendations. Your resume looks fair.")

    # ── TAB: Raw resume ───────────────────────────────────────────────
    with tab_raw:
        st.subheader("Extracted Resume Text")
        st.text_area(
            "Full text",
            st.session_state.resume_text or "",
            height=500,
            disabled=True,
        )
else:
    # Landing page
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
            ### Smart Skill Extraction
            RoBERTa NER + dictionary matching detects skills
            across every section of your resume with proficiency levels.
            """
        )
    with col2:
        st.markdown(
            """
            ### Smart Role Mapping
            Maps your skills to 40+ job roles across CS, AI/ML,
            Electrical, Mechanical, Civil, Chemical, and more.
            """
        )
    with col3:
        st.markdown(
            """
            ### Fairness Detection
            Identifies gender, age, ethnicity, and education bias
            in your resume with actionable recommendations.
            """
        )
    st.markdown("---")
    col4, col5, col6 = st.columns(3)
    with col4:
        st.markdown(
            """
            ### Skill Gap Analysis
            Compares your skills against market demand and
            prioritises what to learn next (High / Medium / Low).
            """
        )
    with col5:
        st.markdown(
            """
            ### Trend Forecasting
            Tracks which skills are surging, stable, or declining
            based on real-time job posting analysis.
            """
        )
    with col6:
        st.markdown(
            """
            ### Get Started
            Upload your resume in the sidebar to begin
            your comprehensive career intelligence analysis.
            """
        )