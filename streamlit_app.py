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
from pathlib import Path

import pandas as pd
import streamlit as st

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
from src.fairness.detector import evaluate_fairness
from src.job_matcher import jobs_df_to_postings, match_resume_to_jobs
from src.models.schemas import (
    ExtractedSkill,
    FairnessReport,
    MatchResult,
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


@st.cache_data(show_spinner="Preparing job postings…")
def _cached_load_postings():
    jobs_df = _cached_load_jobs()
    if jobs_df.empty:
        return []
    return jobs_df_to_postings(jobs_df)


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
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.6rem; font-weight: 800;
        background: linear-gradient(120deg, #1f77b4, #2ecc71);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; margin-bottom: .3rem;
    }
    .subtitle { text-align:center; color:#7f8c8d; font-size:1.1rem; margin-bottom:1.5rem; }
    .metric-card {
        background: #f8f9fa; border-radius: 10px; padding: 1rem 1.2rem;
        border-left: 4px solid #1f77b4; margin-bottom: .6rem;
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
    "Skills &bull; Matching &bull; Gaps &bull; Trends &bull; Fairness</div>",
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
        "matches",
        "role_matches",
        "gaps",
        "trends",
        "fairness",
        "comprehensive_gap_analysis",
        "match_explanations",
        "role_explanations",
    ):
        if key not in st.session_state:
            st.session_state[key] = None


_init_state()

# Heavy resources are loaded lazily during analysis to keep startup fast.
_jobs_df = None
_gap_analyzer = None


# ---------------------------------------------------------------------------
# Sidebar — upload + options
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("📂 Upload Resume")
    uploaded = st.file_uploader(
        "PDF, DOCX, or TXT",
        type=["pdf", "docx", "txt"],
        help="Upload your resume to begin analysis.",
    )
    st.divider()
    st.subheader("⚙️ Options")
    use_ner = st.toggle("Use NER extraction", value=False, help="RoBERTa NER improves extraction but makes analysis slower.")
    top_n = st.slider("Top N role suggestions", 5, 30, 10)
    min_score = st.slider("Minimum match score", 0, 80, 10, step=5)
    
    st.divider()
    st.subheader("🎓 Learning Preferences")
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

    st.divider()
    run_btn = st.button("🚀 Analyse Resume", type="primary", use_container_width=True)

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
        st.write("📄 Extracting text…")
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
        st.write("🔍 Extracting skills…")
        skills = extract_skills(text, use_ner=use_ner)
        st.session_state.skills = skills
        skill_names = [s.canonical for s in skills]

        # 3 — Role mapping
        st.write("🔗 Mapping suitable job roles…")
        role_matches = match_roles(skill_names, min_score=min_score, top_n=top_n)
        st.session_state.role_matches = role_matches

        # 4 — Job matching
        st.write("🎯 Matching job postings…")
        postings = _cached_load_postings()
        matches = match_resume_to_jobs(
            text,
            skill_names,
            postings,
            top_n=top_n,
            min_score=float(min_score),
            use_semantic=False,
        )
        st.session_state.matches = matches

        # 4b — SHAP explainability
        st.write("🧠 Building SHAP explanations…")
        try:
            explainer = MatchSHAPExplainer()
            st.session_state.match_explanations = explainer.explain_job_matches(
                text,
                skill_names,
                matches[:3],
                postings,
            )
            st.session_state.role_explanations = explainer.explain_role_matches(
                text,
                skill_names,
                role_matches[:3],
            )
        except Exception as exc:
            st.warning(f"Explainability fallback activated: {str(exc)[:180]}")
            st.session_state.match_explanations = {}
            st.session_state.role_explanations = {}

        # 5 — Skill gaps
        st.write("📊 Analysing skill gaps…")
        if _jobs_df is not None and not _jobs_df.empty:
            gaps = rank_skill_gaps(skill_names, _jobs_df, top_n=15)
            trends = get_skill_trends(_jobs_df)
        else:
            gaps = []
            trends = []
        st.session_state.gaps = gaps
        st.session_state.trends = trends

        # 5b — Comprehensive skill gap analysis
        st.write("📊 Running comprehensive gap analysis…")
        comprehensive_analysis = None
        try:
            # Try to use cached analyzer first
            if _gap_analyzer is not None:
                analyzer_to_use = _gap_analyzer
                st.write("  Using cached analyzer…")
            else:
                # If not cached, try to load it now
                st.write("  Loading gap analyzer…")
                from src.skill_gap_analysis import SkillGapAnalysis
                analyzer_to_use = SkillGapAnalysis()
            
            # Run analysis only if we have role matches and skills
            if role_matches and skill_names and analyzer_to_use:
                st.write("  Computing priority rankings, learning paths, and quick wins…")
                top_role = role_matches[0]
                job_data = {
                    'role': top_role.role,
                    'description': top_role.description,
                    'core_skills': list(set(top_role.matched_core + top_role.missing_core)),
                    'optional_skills': list(set(top_role.matched_optional)),
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
                st.write("  ✅ Comprehensive analysis complete!")
            else:
                st.write("  ⚠️ Skipping (need matched roles and skills)")
        except Exception as e:
            import traceback
            st.error(f"Gap analysis error: {str(e)[:200]}")
            if st.checkbox("Show full error trace"):
                st.code(traceback.format_exc())

        # 6 — Trends
        st.write("📈 Computing trends…")

        # 7 — Fairness
        st.write("⚖️ Evaluating fairness…")
        fairness = evaluate_fairness(text)
        st.session_state.fairness = fairness

        status.update(label="Analysis complete!", state="complete", expanded=False)

elif run_btn and uploaded is None:
    st.warning("Please upload a resume first.")

# ---------------------------------------------------------------------------
# Render results — tabbed layout
# ---------------------------------------------------------------------------

if st.session_state.skills is not None:
    tab_skills, tab_roles, tab_gaps, tab_trends, tab_fair, tab_raw, tab_matches = st.tabs(
        ["🔍 Skills", "🎯 Suitable Roles", "📊 Skill Gaps", "📈 Trends", "⚖️ Fairness", "📝 Resume Text"]
        + ["Top Matches"]
    )

    # ── TAB: Skills ────────────────────────────────────────────────────
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
        cols = st.columns(4)
        prof_counts = {"advanced": 0, "intermediate": 0, "basic": 0}
        for s in skills:
            prof_counts[s.proficiency] = prof_counts.get(s.proficiency, 0) + 1
        cols[0].metric("Total Skills", len(skills))
        cols[1].metric("Advanced", prof_counts.get("advanced", 0))
        cols[2].metric("Intermediate", prof_counts.get("intermediate", 0))
        cols[3].metric("Basic", prof_counts.get("basic", 0))

        # Category cards
        for cat_name in list(cat_map.keys()) + (["Other"] if uncategorised else []):
            cat_skills = cat_map.get(cat_name, uncategorised)
            if not cat_skills:
                continue
            with st.expander(f"**{cat_name}** ({len(cat_skills)})", expanded=True):
                chips_html = ""
                for s in sorted(cat_skills, key=lambda x: x.canonical):
                    cls = f"chip-{s.proficiency}"
                    chips_html += (
                        f'<span class="skill-chip {cls}" title="Section: {s.source_section} | '
                        f'Proficiency: {s.proficiency}">{s.canonical}</span>'
                    )
                st.markdown(chips_html, unsafe_allow_html=True)

        # Tabular detail
        with st.expander("📋 Detailed skill table"):
            df = pd.DataFrame([s.model_dump() for s in skills])
            st.dataframe(df, use_container_width=True, hide_index=True)

    # ── TAB: Suitable Roles ─────────────────────────────────────────
    with tab_matches:
        matches: list[MatchResult] = st.session_state.matches or []
        st.subheader(f"Top Job Matches ({len(matches)})")

        if not matches:
            st.info("No job matches found yet. Try lowering the minimum score or uploading a resume with clearer skills.")
        else:
            top_match = matches[0]
            summary_cols = st.columns(4)
            summary_cols[0].metric("Best Match", top_match.job.title)
            summary_cols[1].metric("Top Score", f"{top_match.overall_score:.1f}%")
            summary_cols[2].metric("Jobs Returned", len(matches))
            summary_cols[3].metric(
                "Avg Score",
                f"{(sum(match.overall_score for match in matches) / len(matches)):.1f}%",
            )

            st.divider()

            for index, match in enumerate(matches, 1):
                with st.expander(
                    f"**#{index} - {match.job.title}** at **{match.job.company}** - {match.overall_score:.1f}%",
                    expanded=index <= 3,
                ):
                    info_cols = st.columns(4)
                    info_cols[0].metric("Overall", f"{match.overall_score:.1f}%")
                    info_cols[1].metric("Skill Fit", f"{match.skill_score:.1f}%")
                    info_cols[2].metric("Experience", f"{match.experience_score:.1f}%")
                    info_cols[3].metric("Semantic", f"{match.semantic_score:.1f}%")

                    meta_parts = [match.job.location, match.job.experience_level]
                    if match.job.remote:
                        meta_parts.append("Remote")
                    st.caption(" | ".join(part for part in meta_parts if part))

                    if match.job.description:
                        preview = match.job.description[:400]
                        if len(match.job.description) > 400:
                            preview += "..."
                        st.write(preview)

                    skill_left, skill_right = st.columns(2)
                    with skill_left:
                        st.markdown("**Matching Skills**")
                        matched_skills = match.matched_required + match.matched_preferred
                        if matched_skills:
                            matched_html = "".join(
                                f'<span class="skill-chip chip-advanced">{skill}</span>'
                                for skill in match.matched_required
                            ) + "".join(
                                f'<span class="skill-chip chip-intermediate">{skill}</span>'
                                for skill in match.matched_preferred
                            )
                            st.markdown(matched_html, unsafe_allow_html=True)
                        else:
                            st.caption("No explicit skill overlap found.")

                    with skill_right:
                        st.markdown("**Missing Required Skills**")
                        if match.missing_required:
                            missing_html = "".join(
                                f'<span class="skill-chip chip-basic">{skill}</span>'
                                for skill in match.missing_required
                            )
                            st.markdown(missing_html, unsafe_allow_html=True)
                        else:
                            st.success("You cover all required skills for this posting.")

                    st.progress(min(match.overall_score / 100.0, 1.0))

                    explanation = (st.session_state.match_explanations or {}).get(match.job.job_id)
                    if explanation:
                        st.markdown("**Why This Match? (SHAP)**")
                        st.caption(explanation.get("summary", ""))

                        exp_cols = st.columns(3)
                        exp_cols[0].metric("Observed Score", f"{explanation.get('match_score', match.overall_score):.1f}%")
                        exp_cols[1].metric("Explained Score", f"{explanation.get('predicted_score', match.overall_score):.1f}%")
                        exp_cols[2].metric("Method", explanation.get("method", "heuristic").upper())

                        pos_factors = explanation.get("positive_factors", [])
                        neg_factors = explanation.get("negative_factors", [])
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

                        chart_rows = [
                            {"Factor": factor["label"], "Impact": factor["impact"]}
                            for factor in pos_factors + neg_factors
                        ]
                        if chart_rows:
                            st.bar_chart(pd.DataFrame(chart_rows), x="Factor", y="Impact")

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
                score_color = "#28a745" if rm.score >= 60 else "#fd7e14" if rm.score >= 35 else "#dc3545"
                with st.expander(
                    f"**#{i} — {rm.role}**  ({rm.domain})  •  Score: {rm.score:.1f}%",
                    expanded=i <= 3,
                ):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Match Score", f"{rm.score:.1f}%")
                    c2.metric("Core Skills Covered", f"{rm.core_match_pct:.0f}%")
                    c3.metric("Total Skills Matched", rm.total_matched)

                    st.caption(rm.description)

                    sk1, sk2 = st.columns(2)
                    with sk1:
                        st.markdown("**✅ Your Matching Skills**")
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
                        st.markdown("**📚 Skills to Learn**")
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

    # ── TAB: Skill Gaps ───────────────────────────────────────────────
    with tab_gaps:
        st.subheader("Skill Gap Analysis")
        
        # Use comprehensive gap analysis if available
        comprehensive = st.session_state.comprehensive_gap_analysis
        gaps: list[SkillGap] = st.session_state.gaps or []

        # Debug: Show what we have
        if st.checkbox("📊 Show Analysis Debug Info"):
            st.write(f"Comprehensive analysis available: {comprehensive is not None}")
            st.write(f"Basic gaps available: {len(gaps) > 0}")
            st.write(f"HAS_GAP_ANALYSIS: {HAS_GAP_ANALYSIS}")
            if comprehensive:
                st.write(f"Comprehensive keys: {list(comprehensive.keys())}")

        if comprehensive and comprehensive.get('ranked_priorities'):
            # ─── COMPREHENSIVE GAP ANALYSIS ────────────────────
            st.success("📊 **Advanced Gap Analysis** — AI-powered comprehensive skill gap evaluation")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            gaps_by_cat = comprehensive.get('gaps_by_category', {})
            ranked_priorities = comprehensive.get('ranked_priorities', [])
            learning_path = comprehensive.get('learning_path', {})
            
            with col1:
                total_gaps = (len(gaps_by_cat.get('critical', [])) + 
                             len(gaps_by_cat.get('important', [])) + 
                             len(gaps_by_cat.get('nice_to_have', [])))
                st.metric("📌 Total Gaps", total_gaps)
            
            with col2:
                st.metric("🔴 Critical", len(gaps_by_cat.get('critical', [])))
            
            with col3:
                st.metric("🟠 Important", len(gaps_by_cat.get('important', [])))
            
            with col4:
                st.metric("🟢 Nice-to-have", len(gaps_by_cat.get('nice_to_have', [])))
            
            # Tabs for different gap analysis views
            gap_tab1, gap_tab2, gap_tab3, gap_tab4 = st.tabs(
                ["🎯 Priority Ranking", "📅 Learning Path", "⚡ Quick Wins", "📊 Breakdown"]
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
                        tier_color = {
                            'CRITICAL': '🔴',
                            'HIGH': '🟠',
                            'MEDIUM': '🟡',
                            'LOW': '🟢',
                        }.get(tier, '⚪')
                        
                        with st.expander(
                            f"{tier_color} **#{idx} — {skill.title()}** "
                            f"(Score: {priority:.1f}/100 • {category})",
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
                                st.markdown(f"**💡 Recommendation:**\n{recommendation}")
                else:
                    st.success("✅ No gaps identified or all high-priority skills already present!")
            
            # ─── TAB 2: LEARNING PATH ────────────────────────
            with gap_tab2:
                st.markdown("### 📅 Month-by-Month Learning Timeline")
                
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
                            st.markdown("#### 🎯 Month-by-Month Milestones")
                            
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
                                    f"({milestone.get('category', 'N/A')}) → {milestone.get('match_score_after', 0):.0f}%",
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
                                            st.write("**🎓 Learning Objectives:**")
                                            for obj in objectives:
                                                st.write(f"  ✓ {obj}")
                                        
                                        # Resources
                                        resources = milestone.get('resources', [])
                                        if resources:
                                            st.write("**📚 Recommended Resources:**")
                                            for resource in resources:
                                                res_name = resource.get('name', 'Resource')
                                                res_type = resource.get('type', 'resource')
                                                res_cost = resource.get('cost', 'N/A')
                                                res_platform = resource.get('platform', 'Online')
                                                st.write(f"  📖 **{res_name}** ({res_platform}) - {res_cost}")
                                        
                                        # Practice projects
                                        projects = milestone.get('practice_projects', [])
                                        if projects:
                                            st.write("**🛠️ Practice Projects:**")
                                            for project in projects:
                                                st.write(f"  ⚙️ {project}")
                                        
                                        # Success criteria
                                        criteria = milestone.get('success_criteria', [])
                                        if criteria:
                                            st.write("**✅ Success Criteria:**")
                                            for criterion in criteria:
                                                st.write(f"  ☑️ {criterion}")
                                    
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
                            st.markdown("#### ⚡ Quick Wins (Start Here!)")
                            for qw in quick_wins:
                                st.success(
                                    f"**{qw.get('skill', 'Skill')}**: {qw.get('why_quick_win', 'High impact')} | "
                                    f"Time: {qw.get('time_needed', 'N/A')}"
                                )
                        
                        # Recommendations
                        recommendations = path_data.get('key_recommendations', [])
                        if recommendations:
                            st.divider()
                            st.markdown("#### 💡 Key Recommendations")
                            for rec in recommendations:
                                st.write(f"✓ {rec}")
                        
                        # Show powered by
                        st.divider()
                        st.caption("✨ Powered by Google Gemini AI - Personalized learning path")
                    
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
                        st.markdown("#### 🎯 Month-by-Month Milestones")
                        
                        # Display milestones with expandable details
                        for idx, milestone in enumerate(milestones[:12], 1):
                            skill_name = milestone.get('skill', 'Unknown')
                            category = milestone.get('category', 'IMPORTANT')
                            duration = milestone.get('duration_months', 0)
                            score_after = milestone.get('match_score_after', 0)
                            difficulty = milestone.get('difficulty', 'moderate')
                            
                            # Color code by category
                            category_emoji = {
                                'CRITICAL': '🔴',
                                'IMPORTANT': '🟠',
                                'NICE_TO_HAVE': '🟢'
                            }.get(category, '⚪')
                            
                            with st.expander(
                                f"Month {milestone.get('month', idx)}: {skill_name.title()} {category_emoji} "
                                f"({category}) → {score_after:.0f}%",
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
                                        st.write("**🎓 Learning Objectives:**")
                                        for obj in objectives:
                                            st.write(f"  ✓ {obj}")
                                    
                                    # Resources
                                    resources = milestone.get('resources', [])
                                    if resources:
                                        st.write("**📚 Recommended Resources:**")
                                        for resource in resources:
                                            res_name = resource.get('name', 'Resource') if isinstance(resource, dict) else resource
                                            res_type = resource.get('type', 'resource').title() if isinstance(resource, dict) else 'Resource'
                                            res_platform = resource.get('platform', 'Online') if isinstance(resource, dict) else 'Online'
                                            res_cost = resource.get('cost', 'varies') if isinstance(resource, dict) else 'varies'
                                            st.write(f"  📖 **{res_name}** ({res_platform}) - {res_cost}")
                                    
                                    # Practice projects
                                    projects = milestone.get('practice_projects', [])
                                    if projects:
                                        st.write("**🛠️ Practice Projects:**")
                                        for project in projects:
                                            st.write(f"  ⚙️ {project}")
                                    
                                    # Success criteria
                                    criteria = milestone.get('success_criteria', [])
                                    if criteria:
                                        st.write("**✅ Success Criteria:**")
                                        for criterion in criteria:
                                            st.write(f"  ☑️ {criterion}")
                                
                                with col_right:
                                    score_improvement = milestone.get('score_improvement', 0)
                                    st.metric(
                                        "Match After",
                                        f"{score_after:.0f}%",
                                        delta=f"+{score_improvement:.0f}%" if score_improvement > 0 else None
                                    )
                else:
                    st.info("📅 Learning path will be generated once gaps are identified")
            
            # ─── TAB 3: QUICK WINS ───────────────────────────────
            with gap_tab3:
                st.markdown("### ⚡ Quick Wins — Learn Fast, High Impact")
                
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
                                    
                                    ✅ **High ROI** — Learn quickly!
                                    """
                                )
                else:
                    st.success("✅ No quick wins needed — you're on track!")
            
            # ─── TAB 4: BREAKDOWN ────────────────────────────────
            with gap_tab4:
                st.markdown("### 📊 Gaps by Category")
                
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
                    st.bar_chart(chart_data.set_index('Category'), use_container_width=True)
                
                with col2:
                    for label, count, color in zip(category_labels, category_counts, ['🔴', '🟠', '🟢']):
                        st.metric(f"{color} {label}", count)
                
                # Detailed list
                for label, skills, emoji in [
                    ('CRITICAL', critical, '🔴'),
                    ('IMPORTANT', important, '🟠'),
                    ('NICE-TO-HAVE', nice, '🟢'),
                ]:
                    if skills:
                        st.markdown(f"### {emoji} {label}")
                        cols = st.columns(3)
                        for idx, skill in enumerate(skills):
                            cols[idx % 3].markdown(f"• {skill.title()}")

        else:
            # Fallback to basic analysis
            st.info("📊 **Basic Gap Analysis** — Standard skill gap evaluation")
            
            # Summary counts
            high = sum(1 for g in gaps if g.priority == "High")
            med = sum(1 for g in gaps if g.priority == "Medium")
            low = sum(1 for g in gaps if g.priority == "Low")
            c1, c2, c3 = st.columns(3)
            c1.metric("🔴 High Priority", high)
            c2.metric("🟠 Medium Priority", med)
            c3.metric("🟢 Low Priority", low)

            # Priority cards
            for priority, emoji in [("High", "🔴"), ("Medium", "🟠"), ("Low", "🟢")]:
                p_gaps = [g for g in gaps if g.priority == priority]
                if not p_gaps:
                    continue
                st.markdown(f"### {emoji} {priority} Priority")
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
        st.subheader("Market Skill Trends")

        if not trends:
            st.info("No trend data available. Ensure job data exists in the processed directory.")
        else:
            relevant_skills: list[str] = []
            top_matches: list[MatchResult] = st.session_state.matches or []
            if top_matches:
                for match in top_matches[:3]:
                    relevant_skills.extend(match.missing_required)
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

            # Top growing
            growing = sorted(trends, key=lambda t: -t.growth_pct)[:10]
            declining = sorted(trends, key=lambda t: t.growth_pct)[:5]

            col_up, col_down = st.columns(2)
            with col_up:
                st.markdown("### 📈 Fastest Growing")
                for t in growing:
                    delta = f"+{t.growth_pct:.1f}%" if t.growth_pct > 0 else f"{t.growth_pct:.1f}%"
                    st.metric(t.skill, f"{t.current_pct:.1f}%", delta=delta)

            with col_down:
                st.markdown("### 📉 Declining")
                for t in declining:
                    if t.growth_pct >= 0:
                        continue
                    st.metric(t.skill, f"{t.current_pct:.1f}%", delta=f"{t.growth_pct:.1f}%")

            # Full table
            st.markdown("### Full Trend Table")
            trend_df = pd.DataFrame([t.model_dump() for t in trends])
            st.dataframe(trend_df, use_container_width=True, hide_index=True)

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
                score_emoji, score_label, score_col = "✅", "Good", "green"
            elif score >= 50:
                score_emoji, score_label, score_col = "⚠️", "Moderate Concerns", "orange"
            else:
                score_emoji, score_label, score_col = "🚨", "Significant Bias Detected", "red"

            st.markdown(
                f"### {score_emoji} Fairness Score: **{score:.0f} / 100** — {score_label}"
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
                st.dataframe(variant_df, use_container_width=True, hide_index=True)

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

                with st.expander("📋 Detailed indicator table"):
                    st.dataframe(ind_df, use_container_width=True, hide_index=True)

            # Recommendations
            if fairness.recommendations:
                st.markdown("### 💡 Recommendations")
                for rec in fairness.recommendations:
                    st.markdown(f"- {rec}")
            else:
                st.success("No bias-related recommendations — your resume looks fair!")

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
            ### 🔍 Smart Skill Extraction
            RoBERTa NER + dictionary matching detects skills
            across every section of your resume with proficiency levels.
            """
        )
    with col2:
        st.markdown(
            """
            ### 🎯 Smart Role Mapping
            Maps your skills to 40+ job roles across CS, AI/ML,
            Electrical, Mechanical, Civil, Chemical, and more.
            """
        )
    with col3:
        st.markdown(
            """
            ### ⚖️ Fairness Detection
            Identifies gender, age, ethnicity, and education bias
            in your resume with actionable recommendations.
            """
        )
    st.markdown("---")
    col4, col5, col6 = st.columns(3)
    with col4:
        st.markdown(
            """
            ### 📊 Skill Gap Analysis
            Compares your skills against market demand and
            prioritises what to learn next (High / Medium / Low).
            """
        )
    with col5:
        st.markdown(
            """
            ### 📈 Trend Forecasting
            Tracks which skills are surging, stable, or declining
            based on real-time job posting analysis.
            """
        )
    with col6:
        st.markdown(
            """
            ### 🚀 Get Started
            Upload your resume in the sidebar to begin
            your comprehensive career intelligence analysis.
            """
        )