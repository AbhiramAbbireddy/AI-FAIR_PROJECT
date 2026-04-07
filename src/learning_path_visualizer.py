"""
Roadmap-style learning path visualizer for Streamlit.
"""
from __future__ import annotations

from html import escape
from urllib.parse import quote_plus

import streamlit as st
import streamlit.components.v1 as components


def _priority_style(score: float) -> dict[str, str]:
    if score >= 85:
        return {"bg": "#FEF3C7", "border": "#D97706", "badge": "#D97706", "label": "Critical"}
    if score >= 70:
        return {"bg": "#FEE2E2", "border": "#DC2626", "badge": "#DC2626", "label": "High"}
    if score >= 50:
        return {"bg": "#E0F2FE", "border": "#0284C7", "badge": "#0284C7", "label": "Medium"}
    return {"bg": "#F0FDF4", "border": "#16A34A", "badge": "#16A34A", "label": "Low"}


def _resource_href(resource: dict) -> str:
    explicit_url = str(resource.get("url", "")).strip()
    if explicit_url.startswith(("http://", "https://")):
        return explicit_url

    url_hint = str(resource.get("url_hint", "")).strip()
    if url_hint:
        return f"https://www.google.com/search?q={quote_plus(url_hint)}"

    name = str(resource.get("name", "learning resource")).strip()
    platform = str(resource.get("platform", "")).strip()
    query = f"{name} {platform}".strip()
    return f"https://www.google.com/search?q={quote_plus(query)}"


def _build_html(roadmap: dict, initial_score: float) -> str:
    milestones = roadmap.get("milestones", [])
    final_score = roadmap.get("final_match_score", 90)
    total_months = roadmap.get("total_months", "?")
    summary = roadmap.get("summary", "")

    cards_html = ""
    for index, milestone in enumerate(milestones):
        style = _priority_style(float(milestone.get("priority_score", 70)))
        month_start = milestone.get("month_start", milestone.get("start_month", milestone.get("month", index + 1)))
        month_end = milestone.get("month_end", milestone.get("end_month", month_start))
        month_label = f"Month {month_start}" if month_start == month_end else f"Months {month_start} - {month_end}"

        resources_html = ""
        for resource in milestone.get("resources", []):
            cost = str(resource.get("cost", ""))
            is_free = "free" in cost.lower()
            href = _resource_href(resource)
            resources_html += f"""
            <a class="resource-item resource-link" href="{escape(href, quote=True)}" target="_blank" rel="noopener noreferrer">
              <span class="res-tag" style="background:{'#dcfce7' if is_free else '#fef3c7'}; color:{'#166534' if is_free else '#854d0e'};">
                {'Free' if is_free else 'Paid'}
              </span>
              <div>
                <div class="resource-name">{escape(str(resource.get('name', 'Resource')))}</div>
                <div class="resource-meta">{escape(str(resource.get('platform', 'Platform')))} · {escape(cost)}</div>
              </div>
            </a>
            """

        projects_html = "".join(
            f'<div class="project-item"><span class="proj-bullet">&#9658;</span>{escape(str(project))}</div>'
            for project in milestone.get("practice_projects", [])
        )
        connector = '<div class="connector"></div>' if index < len(milestones) - 1 else ""

        cards_html += f"""
        <div class="milestone-wrapper">
          <div class="spine-dot" style="border-color:{style['border']};"></div>
          <div class="milestone-card" style="border-color:{style['border']}; background:{style['bg']}">
            <div class="card-header">
              <div class="skill-title">{escape(str(milestone.get('skill', 'Skill')))}</div>
              <div class="badges">
                <span class="badge" style="background:{style['badge']}; color:#fff;">{style['label']}</span>
                <span class="score-badge">+{milestone.get('score_improvement', 0)}% -> {milestone.get('match_score_after', final_score)}%</span>
              </div>
            </div>
            <div class="month-label">{month_label} · Priority {float(milestone.get('priority_score', 70)):.0f}/100</div>
            <details>
              <summary class="toggle-summary">Resources &amp; projects</summary>
              <div class="card-body">
                <div class="section-label">Learning resources</div>
                <div class="resources-list">{resources_html}</div>
                <div class="section-label" style="margin-top:12px;">Practice projects</div>
                <div class="projects-list">{projects_html}</div>
              </div>
            </details>
          </div>
        </div>
        {connector}
        """

    score_gain = final_score - initial_score
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  color: #111827;
  background: transparent;
  padding: 4px 2px 24px;
}}
* {{ box-sizing: border-box; }}
.stats-row {{
  display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-bottom:16px;
}}
.stat-card {{
  flex:1; min-width:80px; background:#fff; border:1px solid #e5e7eb; border-radius:10px; padding:10px 12px; text-align:center;
}}
.stat-card.accent {{ border-color:#6366f1; background:#eef2ff; }}
.stat-label {{ font-size:11px; color:#6b7280; margin-bottom:3px; }}
.stat-value {{ font-size:20px; font-weight:700; }}
.summary {{
  background:#f8f9fa; border-left:3px solid #6366f1; padding:10px 12px; border-radius:0 8px 8px 0; margin-bottom:16px;
}}
.start-node, .goal-node {{
  display:flex; align-items:center; gap:12px; border-radius:12px; padding:12px 16px;
}}
.start-node {{ background:#eef2ff; border:1.5px solid #6366f1; }}
.goal-node {{ background:#ecfdf5; border:1.5px solid #16a34a; margin-top:0; }}
.roadmap {{ position:relative; padding-left:28px; }}
.roadmap::before {{
  content:''; position:absolute; left:8px; top:0; bottom:0; width:2px; background:#c7d2fe;
}}
.spine-cap {{ position:relative; height:20px; margin-left:-20px; }}
.spine-cap::before {{ content:''; position:absolute; left:8px; top:0; bottom:0; width:2px; background:#c7d2fe; }}
.milestone-wrapper {{ position:relative; }}
.spine-dot {{
  position:absolute; left:-22px; top:15px; width:14px; height:14px; border-radius:50%; border:2.5px solid; background:#fff; z-index:2;
}}
.connector {{ height:16px; }}
.milestone-card {{
  border:1.5px solid; border-radius:12px; padding:13px 15px;
}}
.card-header {{ display:flex; justify-content:space-between; gap:10px; align-items:flex-start; }}
.skill-title {{ font-size:15px; font-weight:700; }}
.badges {{ display:flex; gap:6px; flex-wrap:wrap; justify-content:flex-end; }}
.badge, .score-badge {{
  font-size:11px; font-weight:700; padding:2px 9px; border-radius:20px;
}}
.score-badge {{ background:rgba(0,0,0,0.06); color:#374151; }}
.month-label {{ font-size:12px; color:#6b7280; margin:6px 0 9px; }}
.toggle-summary {{ font-size:12px; color:#6366f1; font-weight:600; cursor:pointer; }}
.card-body {{ margin-top:12px; padding-top:12px; border-top:1px solid rgba(0,0,0,0.08); }}
.section-label {{ font-size:11px; font-weight:700; text-transform:uppercase; color:#374151; margin-bottom:8px; }}
.resources-list, .projects-list {{ display:flex; flex-direction:column; gap:7px; }}
.resource-item, .project-item {{
  display:flex; gap:8px; background:rgba(255,255,255,0.75); border-radius:8px; border:1px solid rgba(0,0,0,0.07); padding:7px 10px;
}}
.resource-link {{
  text-decoration:none; color:inherit; transition:transform 0.12s ease, box-shadow 0.12s ease, border-color 0.12s ease;
}}
.resource-link:hover {{
  transform:translateY(-1px); box-shadow:0 4px 14px rgba(0,0,0,0.08); border-color:rgba(99,102,241,0.35);
}}
.resource-link:focus {{
  outline:2px solid #6366f1; outline-offset:2px;
}}
.res-tag {{ font-size:10px; font-weight:700; padding:2px 7px; border-radius:4px; white-space:nowrap; }}
.resource-name {{ font-size:13px; font-weight:600; }}
.resource-meta {{ font-size:11px; color:#6b7280; margin-top:2px; }}
.proj-bullet {{ color:#6366f1; font-size:10px; margin-top:3px; }}
</style>
</head>
<body>
{"<div class='summary'>" + escape(summary) + "</div>" if summary else ""}
<div class="stats-row">
  <div class="stat-card"><div class="stat-label">Current match</div><div class="stat-value">{initial_score:.0f}%</div></div>
  <div class="stat-card accent"><div class="stat-label">After roadmap</div><div class="stat-value">{final_score}%</div></div>
  <div class="stat-card"><div class="stat-label">Total gain</div><div class="stat-value">+{score_gain:.0f}%</div></div>
  <div class="stat-card"><div class="stat-label">Duration</div><div class="stat-value">{total_months} mo</div></div>
</div>
<div class="start-node"><div>Start - {initial_score:.0f}% match</div></div>
<div class="spine-cap"></div>
<div class="roadmap">{cards_html}</div>
<div class="spine-cap"></div>
<div class="goal-node"><div>Goal - {final_score}% match in {total_months} months</div></div>
</body>
</html>"""


def _estimate_height(roadmap: dict) -> int:
    return 340 + len(roadmap.get("milestones", [])) * 120


def render_learning_path(roadmap: dict, initial_score: float) -> None:
    if not roadmap.get("milestones"):
        st.warning("No milestones found in the roadmap.")
        return
    components.html(_build_html(roadmap, initial_score), height=_estimate_height(roadmap), scrolling=False)
