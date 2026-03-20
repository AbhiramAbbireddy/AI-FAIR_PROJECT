# FAIR-PATH

FAIR-PATH is an AI-powered resume matching system that helps job seekers understand:

- which roles/jobs fit their profile
- why they received a match score
- which skills are missing
- what to learn first
- which skills are rising or declining in the market
- whether the system is behaving fairly

## Current Project Status

The repository has been refactored around canonical components for:

- resume parsing
- skill extraction
- role/job matching
- SHAP-based explainability
- trend forecasting
- priority ranking
- fairness evaluation
- evaluation reporting

The LLM learning-path generator and Mermaid.js visual roadmap are intentionally skipped for now.

## Canonical Modules

- `src/resume_parser.py`
- `src/skill_extractor.py`
- `src/job_roles_database.py`
- `src/job_matcher.py`
- `src/shap_explainer.py`
- `src/trend_forecaster.py`
- `src/priority_ranker.py`
- `src/fairness_evaluator.py`
- `src/generate_results_summary.py`

## App Entrypoints

- Streamlit UI: `streamlit_app.py`
- FastAPI backend: `src/api/app.py`

## Local Setup

### 1. Create and activate a virtual environment

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Run the Streamlit app

```powershell
streamlit run streamlit_app.py
```

### 4. Run the API

```powershell
uvicorn src.api.app:app --reload --port 8000
```

## Main Features

### 1. Resume Parsing

- extracts resume text
- detects email and phone
- estimates experience years

### 2. Skill Extraction

- keyword/alias-based extraction
- optional NER-assisted extraction
- normalized canonical skills

### 3. Matching

- role matching against curated role profiles
- job matching against parsed job postings
- match score breakdown for skills and experience

### 4. Explainability

- SHAP-based explanation for why a resume matches a role/job
- positive and negative drivers shown in the UI

### 5. Trend Forecasting

- current demand by skill
- monthly trend comparison
- rising/stable/declining labels

### 6. Priority Ranking

- weighted scoring using:
  - job importance
  - market demand
  - learning ease
  - salary impact

### 7. Fairness

- detects demographic-bias signals in resume text
- shows mitigation score and anonymized preview
- reports simple synthetic DPD-style fairness indicators

### 8. Evaluation

- skill extraction evaluation
- matching evaluation
- SHAP explanation proxy evaluation
- trend backtest
- priority ranking proxy evaluation
- fairness evaluation
- master results summary

## Evaluation Scripts

These scripts generate JSON outputs under `results/` and a markdown summary report:

- `src/evaluate_roberta.py`
- `src/evaluate_matching.py`
- `src/evaluate_shap.py`
- `src/evaluate_trends.py`
- `src/evaluate_priorities.py`
- `src/evaluate_fairness.py`
- `src/generate_results_summary.py`

## Notes Before Pushing

- The repo is configured for `venv` only. `uv` files were removed.
- `.env`, local caches, raw datasets, processed datasets, and generated result files are ignored.
- If you want to publish sample outputs to GitHub, remove or adjust the relevant rules in `.gitignore`.
- If your local `.venv` is broken, recreate it before running tests or generating reports.
