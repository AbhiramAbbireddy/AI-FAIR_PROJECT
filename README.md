# FAIR-PATH — Fair, Explainable AI Career Intelligence

> Match resumes to the right roles, explain every score, surface the real gaps, and turn career advice into an actionable roadmap.

[![Repo](https://img.shields.io/badge/Repo-AbhiramAbbireddy%2FFAIR--PATH-gray?style=flat-square)](https://github.com/AbhiramAbbireddy)
[![Frontend](https://img.shields.io/badge/Frontend-Streamlit-red?style=flat-square)](https://streamlit.io)
[![Explainability](https://img.shields.io/badge/Explainability-SHAP-blue?style=flat-square)](https://shap.readthedocs.io)
[![LLM](https://img.shields.io/badge/LLM-Groq%20Llama%203.3-orange?style=flat-square)](https://console.groq.com)
[![Matching](https://img.shields.io/badge/Matching-Proficiency%20Aware-brightgreen?style=flat-square)](#what-makes-fair-path-different)
[![Trends](https://img.shields.io/badge/Market-Temporal%20Dynamics-purple?style=flat-square)](#core-capabilities)
[![Fairness](https://img.shields.io/badge/Fairness-Bias%20Aware-teal?style=flat-square)](#core-capabilities)

---

## The Problem

Most resume tools do one thing: keyword matching.

They tell you that you are a `75% match` for something, but they do not tell you:

- why the score is 75 instead of 45
- which missing skills matter most
- whether those skills are actually rising in the market
- whether your GitHub portfolio supports your claims
- whether you are interview-ready even if the match looks good
- how the role may evolve over the next 6-12 months
- whether the system is making biased decisions

That makes them good for filtering, but poor for career decision-making.

---

## The Solution

FAIR-PATH is an end-to-end AI career intelligence system built around role matching, explainability, fairness, and next-step guidance.

Given a resume, it can:

- parse and structure resume content
- extract and normalize technical skills
- estimate proficiency instead of treating every skill as binary
- map the candidate to suitable job roles
- explain why a role fits using SHAP
- identify missing skills and rank them by priority
- build learning paths and dependency-aware skill graphs
- validate skill claims against GitHub portfolio evidence
- generate interview preparation for weak areas
- forecast role requirement drift over time
- simulate long-term career paths
- assess fairness and bias sensitivity

---

## Architecture

```text
 Phase 1 — Resume Understanding
 ┌──────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
 │ Resume Parser    │   │ Skill Extractor     │   │ Proficiency Estimator│
 │ PDF/TXT -> text  │   │ RoBERTa + aliases   │   │ context-aware levels │
 └────────┬─────────┘   └──────────┬──────────┘   └──────────┬──────────┘
          └────────────────────────┴──────────────────────────┘
                                   │
                         ┌─────────▼─────────┐
                         │ Candidate Profile │
                         │ skills + evidence │
                         └─────────┬─────────┘

 Phase 2 — Matching + Explanation
                         ┌─────────▼─────────┐
                         │ Role Matcher      │  role_mapping/matcher.py
                         │ proficiency-aware │
                         └─────────┬─────────┘
                                   │
                         ┌─────────▼─────────┐
                         │ SHAP Explainer    │  shap_explainer.py
                         │ why this role fits│
                         └─────────┬─────────┘

 Phase 3 — Career Guidance
      ┌───────────────────────┬───────────────────────┬────────────────────────┐
      │ Skill Gap Analysis    │ Trend Forecasting     │ Skill Graph            │
      │ priority ranking      │ rising/declining      │ dependencies + paths   │
      └──────────┬────────────┴───────────┬───────────┴───────────┬────────────┘
                 │                        │                       │
      ┌──────────▼──────────┐   ┌────────▼─────────┐   ┌─────────▼──────────┐
      │ Learning Path       │   │ Temporal Role    │   │ Career Trajectory  │
      │ roadmap + validator │   │ Dynamics         │   │ 1y / 3y / 5y       │
      └──────────┬──────────┘   └────────┬─────────┘   └─────────┬──────────┘
                 │                       │                       │
      ┌──────────▼──────────┐   ┌────────▼─────────┐   ┌─────────▼──────────┐
      │ Portfolio Analyzer  │   │ Interview Agent  │   │ Fairness Evaluator │
      │ GitHub validation   │   │ mock prep        │   │ bias checks        │
      └─────────────────────┘   └──────────────────┘   └────────────────────┘

 Phase 4 — Product Layer
                         ┌──────────────────────────────┐
                         │ Streamlit UI                │  streamlit_app.py
                         │ Summary + tabs + export     │
                         └──────────────────────────────┘
```

---

## What Makes FAIR-PATH Different

### 1. Proficiency-aware matching

Most systems ask: does the resume mention Python?

FAIR-PATH asks: what level of Python does this resume actually demonstrate?

It uses context, action verbs, project evidence, and experience signals to estimate:

- `basic`
- `intermediate`
- `advanced`
- `expert`

That means:

```text
Old systems:
Python mentioned -> full credit

FAIR-PATH:
Python mentioned in coursework only -> partial credit
Python used in shipped projects + strong evidence -> much higher credit
```

### 2. Portfolio-backed validation

The system does not stop at self-claimed skills.

If the user has a GitHub profile, FAIR-PATH checks whether the portfolio actually supports those claims through:

- repository signals
- language evidence
- documentation quality
- activity and recency
- project-level skill validation

### 3. Explainable career guidance

The project combines:

- role matching
- SHAP explanations
- skill priorities
- market drift
- interview prep
- learning validation
- long-term path simulation

So the output is not just “you match this role,” but:

```text
You fit this role now.
These 3 skills are holding you back.
This one matters most.
This other one is rising toward required.
Your portfolio does not prove it yet.
Your interview readiness is here.
If you improve it, this is your likely 5-year path.
```

---

## Setup and Run

### Prerequisites

- Python 3.10 or higher
- `pip`
- Git installed and available in PATH
- Optional: Groq API key for LLM-powered roadmap generation
- Optional: GitHub token for better portfolio-analysis rate limits

### Step 1 — Clone the repo

```bash
git clone <your-repo-url>
cd AI-FAIR_PROJECT
```

### Step 2 — Create and activate virtual environment

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Mac / Linux
source .venv/bin/activate
```

### Step 3 — Install dependencies

```bash
python -m pip install -r requirements.txt
```

### Step 4 — Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
GITHUB_TOKEN=your_github_token
```

Notes:

- `GROQ_API_KEY` is optional, but recommended for LLM learning path generation.
- `GITHUB_TOKEN` is optional, but helps avoid low-rate-limit GitHub API access.
- `.env` is already ignored by Git.

### Step 5 — Launch the app

```bash
streamlit run streamlit_app.py
```

The app opens at:

```text
http://localhost:8501
```

---

## Recommended Flow

1. Upload a resume
2. Let FAIR-PATH parse and extract skills
3. Review the `Summary` tab first
4. Inspect `Suitable Roles` and `Why This Role Fits`
5. Check `Skill Gaps`, `Learning Validator`, and `Career Paths`
6. Use `Portfolio`, `Interview Prep`, and `Trends` to refine next actions
7. Export the report from the `Summary` tab

---

## Core Capabilities

### Resume Parsing

- PDF/TXT resume parsing
- email and phone extraction
- experience-years estimation

File:
- `src/resume_parser.py`

### Skill Extraction

- RoBERTa-assisted extraction
- alias and normalization fallback
- canonical skill mapping
- proficiency estimation with contextual evidence

Files:
- `src/skill_extractor.py`
- `src/skill_extraction/extractor.py`
- `src/skill_extraction/proficiency.py`

### Role Matching

- 200+ curated job-role profiles
- proficiency-aware role scoring
- domain-sensitive AI/ML boosts

Files:
- `src/job_roles_database.py`
- `src/role_mapping/matcher.py`

### SHAP Explainability

- explains why a resume matched a role
- positive and negative contribution factors
- role-level explanation summaries

File:
- `src/shap_explainer.py`

### Skill Gaps and Priority Ranking

- identifies missing skills
- ranks them by impact
- blends demand, importance, learning ease, and salary signal

Files:
- `src/skill_gap_analysis.py`
- `src/priority_ranker.py`

### Dynamic Skill Graph

- dependency-aware skill paths
- bottleneck skill detection
- substitute-skill suggestions
- Mermaid dependency maps

File:
- `src/skill_graph.py`

### Learning Path + Continuous Validation

- milestone-based roadmap
- checkpoint generation
- self-assessment scoring
- next-step feedback

Files:
- `src/llm_learning_path_generator.py`
- `src/learning_path_visualizer.py`
- `src/continuous_learning_validator.py`

### Portfolio Impact Analyzer

- GitHub username extraction
- public repository analysis
- portfolio score
- verified vs weak skill evidence

File:
- `src/portfolio_analyzer.py`

### Interview Preparation Agent

- skill-focused interview questions
- mock-answer evaluation
- feedback and missing points

File:
- `src/interview_preparation_agent.py`

### Temporal Job Market Dynamics

- role requirement drift
- optional skills moving toward required
- projected match decay if the user does not upskill

File:
- `src/temporal_job_dynamics.py`

### Career Trajectory Simulation

- compares top role paths
- estimates 1-year, 3-year, and 5-year outcomes
- includes risk, ROI, and salary outlook

File:
- `src/career_trajectory_simulator.py`

### Fairness Evaluation

- lexical bias scanning
- anonymization-based mitigation
- synthetic demographic sensitivity
- fairness score + DPD signal

Files:
- `src/fairness_evaluator.py`
- `src/fairness/detector.py`

### Executive Summary + Export

- unified summary tab
- next-action recommendations
- downloadable Markdown career report

File:
- `src/report_exporter.py`

---

## Streamlit Experience

The app currently includes these top-level tabs:

- `Summary`
- `Skills`
- `Suitable Roles`
- `Portfolio`
- `Interview Prep`
- `Learning Validator`
- `Career Paths`
- `Skill Gaps`
- `Trends`
- `Fairness`
- `Resume Text`

Inside `Skill Gaps`, there are focused sub-tabs for:

- `Priority Ranking`
- `Learning Path`
- `Skill Graph`
- `Quick Wins`
- `Breakdown`

---

## Example Output Story

```text
Top role: LLM Engineer - 74% match

Why:
- strong Python and AI project signals
- proven LangChain / RAG exposure
- missing Docker and deployment depth

What to learn first:
1. Docker
2. Deployment / MLOps
3. Cloud basics

What the market says:
- Docker is rising
- deployment skills are strengthening toward required

What your portfolio says:
- AI claims are credible
- deployment proof is still weak

What interviews say:
- concept knowledge is decent
- scenario depth is weaker on production systems

What the long-term path says:
- LLM Engineer has the highest upside among your current matches
```

---

## Project Structure

```text
AI-FAIR_PROJECT/
|
|-- streamlit_app.py                     # Main Streamlit product UI
|-- requirements.txt
|-- .gitignore
|
|-- src/
|   |-- resume_parser.py
|   |-- skill_extractor.py
|   |-- job_roles_database.py
|   |-- shap_explainer.py
|   |-- trend_forecaster.py
|   |-- priority_ranker.py
|   |-- skill_gap_analysis.py
|   |-- skill_graph.py
|   |-- llm_learning_path_generator.py
|   |-- learning_path_visualizer.py
|   |-- continuous_learning_validator.py
|   |-- portfolio_analyzer.py
|   |-- interview_preparation_agent.py
|   |-- temporal_job_dynamics.py
|   |-- career_trajectory_simulator.py
|   |-- fairness_evaluator.py
|   |-- report_exporter.py
|   |
|   |-- role_mapping/
|   |   |-- matcher.py
|   |   |-- role_database.py
|   |
|   |-- skill_extraction/
|   |   |-- extractor.py
|   |   |-- normalizer.py
|   |   |-- proficiency.py
|   |
|   |-- models/
|       |-- schemas.py
|
|-- tests/
|   |-- test_resume_parser.py
|   |-- test_skill_extractor_component.py
|   |-- test_job_roles_database_component.py
|   |-- test_job_matcher_component.py
|   |-- test_shap_explainer_component.py
|   |-- test_trend_forecaster_component.py
|   |-- test_priority_ranker_component.py
|   |-- test_fairness_evaluator_component.py
|   |-- test_portfolio_analyzer_component.py
|   |-- test_interview_preparation_agent_component.py
|   |-- test_skill_graph_component.py
|   |-- test_temporal_job_dynamics_component.py
|   |-- test_continuous_learning_validator_component.py
|   |-- test_career_trajectory_simulator_component.py
|   |-- test_report_exporter_component.py
```

---

## Evaluation and Reporting

The project includes dedicated evaluation scripts for:

- skill extraction
- role matching
- SHAP explainability
- trends
- priorities
- fairness
- summary reporting

Files:

- `src/evaluate_roberta.py`
- `src/evaluate_matching.py`
- `src/evaluate_shap.py`
- `src/evaluate_trends.py`
- `src/evaluate_priorities.py`
- `src/evaluate_fairness.py`
- `src/generate_results_summary.py`

---

## Notes

- The project is now `venv`-only. `uv` project files were removed.
- `.env`, local caches, generated results, and local runtime data are ignored in Git.
- Groq-powered roadmap generation gracefully falls back if the key or package is unavailable.
- GitHub portfolio analysis also degrades safely if the API is unavailable.
- Some advanced outputs are heuristic/rule-based by design unless live model access is available.

---

## License

MIT
