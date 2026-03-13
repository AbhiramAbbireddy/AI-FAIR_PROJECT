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
from src.forecasting.trend_forecaster import compute_current_demand, get_skill_trends
from src.job_pipeline.collector import JobCollector, load_static_jobs
from src.matching.semantic_matcher import match_resume_to_jobs
from src.models.schemas import (
    ExtractedSkill,
    FairnessReport,
    MatchResult,
    SkillGap,
    SkillTrend,
)
from src.role_mapping.matcher import match_roles, RoleMatch
from src.skill_extraction.extractor import extract_skills, extract_text
from src.skill_gap.ranker import rank_skill_gaps


# ---------------------------------------------------------------------------
# Cached loaders — run only once across reruns
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner="Loading Sentence-BERT model…")
def _load_sbert():
    """Pre-load SBERT so matching doesn't pay the startup cost."""
    from src.matching.semantic_matcher import _get_sbert
    return _get_sbert()


@st.cache_data(show_spinner="Loading job database…")
def _cached_load_jobs():
    import os
    from src.config.settings import JOBS_PARSED_PATH
    from src.job_pipeline.collector import load_static_jobs
    if os.path.exists(JOBS_PARSED_PATH):
        jobs_df = pd.read_csv(JOBS_PARSED_PATH, nrows=5000)
    else:
        jobs_df = pd.DataFrame()
    postings = load_static_jobs(max_rows=5000)
    return jobs_df, postings

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
        "skills",
        "matches",
        "role_matches",
        "gaps",
        "trends",
        "fairness",
    ):
        if key not in st.session_state:
            st.session_state[key] = None


_init_state()

# Pre-load expensive resources on first run
_load_sbert()
_jobs_df, _postings = _cached_load_jobs()


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
    use_ner = st.toggle("Use NER extraction", value=True, help="RoBERTa NER for contextual skill detection.")
    top_n = st.slider("Top N role suggestions", 5, 30, 10)
    min_score = st.slider("Minimum match score", 0, 80, 10, step=5)

    st.divider()
    run_btn = st.button("🚀 Analyse Resume", type="primary", use_container_width=True)

    st.markdown("---")
    st.caption("FAIR-PATH v2.0 — AI Career Intelligence")

# ---------------------------------------------------------------------------
# Main analysis pipeline
# ---------------------------------------------------------------------------

if run_btn and uploaded is not None:

    with st.status("Running full analysis…", expanded=True) as status:
        # 1 — Extract text
        st.write("📄 Extracting text…")
        ext = os.path.splitext(uploaded.name)[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext or ".pdf") as tmp:
            tmp.write(uploaded.getvalue())
            tmp_path = tmp.name
        try:
            text = extract_text(tmp_path, filename=uploaded.name)
        finally:
            os.unlink(tmp_path)

        if not text or len(text.strip()) < 30:
            st.error("Could not extract meaningful text from the file.")
            st.stop()
        st.session_state.resume_text = text

        # 2 — Skill extraction
        st.write("🔍 Extracting skills…")
        skills = extract_skills(text, use_ner=use_ner)
        st.session_state.skills = skills
        skill_names = [s.canonical for s in skills]

        # 3 — Role mapping
        st.write("🔗 Mapping suitable job roles…")
        role_matches = match_roles(skill_names, min_score=min_score, top_n=top_n)
        st.session_state.role_matches = role_matches

        # 4 — Skill gaps
        st.write("📊 Analysing skill gaps…")
        if _jobs_df is not None and not _jobs_df.empty:
            gaps = rank_skill_gaps(skill_names, _jobs_df, top_n=15)
        else:
            gaps = []
        st.session_state.gaps = gaps

        # 5 — Trends
        st.write("📈 Computing trends…")
        if _jobs_df is not None and not _jobs_df.empty:
            trends = get_skill_trends(_jobs_df)
        else:
            trends = []
        st.session_state.trends = trends

        # 6 — Fairness
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
    tab_skills, tab_roles, tab_gaps, tab_trends, tab_fair, tab_raw = st.tabs(
        ["🔍 Skills", "🎯 Suitable Roles", "📊 Skill Gaps", "📈 Trends", "⚖️ Fairness", "📝 Resume Text"]
    )

    # ── TAB: Skills ────────────────────────────────────────────────────
    with tab_skills:
        skills: list[ExtractedSkill] = st.session_state.skills
        st.subheader(f"Extracted Skills ({len(skills)})")

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

    # ── TAB: Skill Gaps ───────────────────────────────────────────────
    with tab_gaps:
        gaps: list[SkillGap] = st.session_state.gaps or []
        st.subheader("Skill Gap Analysis")

        if not gaps:
            st.info("No skill gap data available. Ensure job data exists in the processed directory.")
        else:
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
