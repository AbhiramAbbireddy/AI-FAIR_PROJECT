# 🎯 FAIR-PATH: AI-Powered Resume-Job Matching System

**Explainable AI system for intelligent resume-job matching with skill gap analysis, trend forecasting, and SHAP explainability.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-latest-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Quick Start (5 Minutes)

### Option 1: One-Click Launch (Windows)
```bash
# Double-click to run everything
LAUNCH.bat
```

### Option 2: Manual Launch
```bash
# 1. Quick test with existing data
uv run python quick_test.py

# 2. Launch UI
uv run streamlit run app.py

# 3. Or run demo
uv run python demo_matching.py --category IT
```

---

## 📋 System Requirements

- **Python:** 3.11 or higher
- **RAM:** 8GB minimum, 16GB recommended
- **Disk:** 5GB free space
- **OS:** Windows/Linux/Mac

### Dependencies
All managed via `uv` (auto-installed):
- PyTorch 2.0+
- Transformers 4.30+
- Streamlit 1.30+
- pandas, scikit-learn, shap, pdfplumber

---

## 🎯 Features

### ✅ Phase 1-2: Data Processing (COMPLETE)
- ✅ **2,484 resumes** processed (24 job categories)
- ✅ **123,849 LinkedIn jobs** parsed
- ✅ **288 comprehensive skills** vocabulary
- ✅ **99.4% extraction success rate**
- ✅ **RoBERTa NER model** (jjzha/jobbert_skill_extraction)

### ✅ Phase 3-4: Matching Engine (COMPLETE)
- ✅ **Weighted matching algorithm** (70% required, 30% preferred)
- ✅ **Real-time UI** with Streamlit
- ✅ **Smart filters** (remote, salary, location, experience)
- ✅ **Auto-validation** system (heuristic-based)
- ✅ **Partial data support** (works during parsing)

### ✅ Phase 5: SHAP Explainability (COMPLETE)
- ✅ **Random Forest** explainability model
- ✅ **SHAP values** for match explanations
- ✅ **Feature importance** visualization
- ✅ **Top positive/negative factors** for each match

### ✅ Phase 6: Trend Forecasting (COMPLETE)
- ✅ **Skill demand analysis** (top 50 trending skills)
- ✅ **Category growth predictions**
- ✅ **Salary trend analysis** by skill
- ✅ **Career recommendations** based on trends

### 🛡️ Production Features
- ✅ **Comprehensive logging** (logs/ directory)
- ✅ **Error handling** with recovery
- ✅ **Auto-refresh** UI (30-second cache)
- ✅ **Progress monitoring** for long-running tasks
- ✅ **Checkpoint support** (resume interrupted jobs)

---

## 📂 Project Structure

```
AI-FAIR_PROJECT/
├── app.py                      # Streamlit UI (main application)
├── demo_matching.py            # CLI demo script
├── quick_test.py               # Fast system validation
├── run_pipeline.py             # Master pipeline orchestrator
├── LAUNCH.bat                  # One-click launcher (Windows)
├── check_progress.py           # Monitor parsing progress
│
├── data/
│   ├── raw/                    # Original datasets
│   │   ├── resumes/           # 2,484 PDF resumes
│   │   └── jobs/              # 123,849 LinkedIn jobs
│   └── processed/             # Processed data
│       ├── skills_vocabulary.csv       # 288 skills
│       ├── resume_skills.csv          # Extracted resume skills
│       ├── jobs_parsed.csv            # Parsed job descriptions
│       ├── skill_trends.csv           # Trending skills
│       ├── category_trends.csv        # Category growth
│       └── salary_trends.csv          # Salary by skill
│
├── src/
│   ├── data_pipeline/
│   │   ├── build_comprehensive_skill_vocabulary.py
│   │   └── extract_resumes.py
│   ├── skill_extraction/
│   │   ├── extract_resume_skills.py   # Hybrid RoBERTa+Dictionary
│   │   └── test_extraction.py
│   ├── matching/
│   │   ├── parse_jobs.py              # Extract job skills
│   │   ├── matcher.py                 # Matching algorithm
│   │   ├── ranker.py                  # Ranking & filtering
│   │   ├── validate.py                # Manual validation
│   │   └── auto_validate.py           # Automated validation
│   ├── explainability/
│   │   └── shap_explainer.py          # SHAP explanations
│   ├── forecasting/
│   │   └── trend_analyzer.py          # Trend predictions
│   └── utils/
│       ├── logger.py                   # Production logging
│       └── error_handler.py            # Error handling
│
├── logs/                       # Application logs
├── docs/                       # Documentation
└── README.md                   # This file
```

---

## 🎮 Usage Examples

### 1. Launch Full UI
```bash
# Start Streamlit interface
uv run streamlit run app.py

# UI features:
# • Browse 2,484 resumes by category
# • See top N job matches with scores
# • Filter by remote, salary, location
# • View skill gap analysis
# • Real-time progress monitoring
```

### 2. Command-Line Demo
```bash
# Test specific category
uv run python demo_matching.py --category IT
uv run python demo_matching.py --category ENGINEERING
uv run python demo_matching.py --category HEALTHCARE

# Test specific resume ID
uv run python demo_matching.py --resume-id 50

# Shows:
# • Top 10 job matches
# • Match scores and breakdowns
# • Filter examples (remote, salary, location)
```

### 3. Validate System
```bash
# Automated validation (100 samples)
cd src/matching
uv run python auto_validate.py

# Manual validation (10 samples)
uv run python validate.py

# Target: Precision@5 > 75%
```

### 4. Analyze Trends
```bash
# Generate trend forecasts
cd src/forecasting
uv run python trend_analyzer.py

# Output:
# • Top 10 in-demand skills
# • Growing job categories
# • Highest-paying skills
# • Career recommendations
```

### 5. Build Explainability
```bash
# Train SHAP explainer
cd src/explainability
uv run python shap_explainer.py

# Output:
# • Trained Random Forest model
# • SHAP values for top matches
# • Feature importance analysis
```

---

## 🔧 Complete Pipeline

### Run Everything from Scratch
```bash
# Full pipeline (all phases)
uv run python run_pipeline.py

# Steps:
# 1. Build vocabulary (1 min)
# 2. Extract resume skills (10 min)
# 3. Parse job descriptions (60 min)
# 4. Validate matching (5 min)
# 5. Build explainability (10 min)

# Skip completed steps (smart mode)
uv run python run_pipeline.py

# Force rerun all steps
uv run python run_pipeline.py --force
```

---

## 📊 Performance Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Resumes Processed | 2,484 | ✅ |
| Success Rate | 99.4% | ✅ Excellent |
| Avg Skills/Resume | 8.1 | ✅ Good |
| Jobs Processed | 123,849 | ✅ |
| Skills Vocabulary | 288 | ✅ Comprehensive |
| Match Speed | <1s per resume | ✅ Fast |
| UI Responsiveness | Real-time | ✅ |
| Validation P@5 | 75%+ | ✅ Target met |

---

## 🎓 Algorithm Details

### Matching Score Calculation
```python
# Weighted scoring (70% required, 30% preferred)
required_score = matched_required / total_required * 100
preferred_score = matched_preferred / total_preferred * 100

final_score = (required_score * 0.7) + (preferred_score * 0.3)
```

### Skill Extraction
- **Method:** Hybrid RoBERTa NER + Dictionary matching
- **Model:** jjzha/jobbert_skill_extraction (domain-specific)
- **Fallback:** Dictionary matching for robustness
- **Result:** 99.4% success rate (vs 85% dictionary-only)

### Explainability
- **Model:** Random Forest Classifier (100 trees)
- **Method:** SHAP TreeExplainer
- **Features:** Match scores, skill presence, job characteristics
- **Output:** Top 5 positive/negative factors per match

---

## 🚨 Troubleshooting

### Issue: "Job data not found"
**Solution:** Job parsing may still be running. Check progress:
```bash
uv run python check_progress.py
```

### Issue: "No matches found"
**Solution:** 
1. Check minimum score threshold (lower it)
2. Verify resume has extracted skills
3. Ensure jobs_parsed.csv exists

### Issue: "Streamlit won't start"
**Solution:**
```bash
# Install/update Streamlit
uv pip install streamlit --upgrade

# Try alternative port
uv run streamlit run app.py --server.port 8502
```

### Issue: "Out of memory"
**Solution:**
1. Close other applications
2. Process jobs in batches (edit parse_jobs.py)
3. Use quick_test.py with subset

---

## 📈 Future Enhancements

### Phase 7: Priority Ranking (3 weeks)
- Multi-factor optimization (skills + salary + location + remote)
- Personalized weighting based on user preferences
- AHP (Analytic Hierarchy Process) implementation

### Phase 8: Fairness Testing (2 weeks)
- Demographic Parity Difference (DPD)
- Equal Opportunity Difference (EOD)
- Bias detection and mitigation

### Phase 9-12: Finalization (4 weeks)
- System integration testing
- Performance optimization
- Research paper writing
- Publication submission

---

## 🤝 Contributing

This is a research project for FAIR-PATH publication. For questions or collaboration:

1. Check `docs/MENTOR_IMPLEMENTATION_GUIDE.md` for detailed architecture
2. Review `logs/` for error tracking
3. Run `quick_test.py` before making changes

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- **Model:** jjzha/jobbert_skill_extraction (Hugging Face)
- **Data:** LinkedIn job postings dataset
- **Skills:** O*NET occupation taxonomy
- **Frameworks:** PyTorch, Transformers, Streamlit, SHAP

---

## 📞 Quick Reference

### Essential Commands
```bash
# Test system
uv run python quick_test.py

# Launch UI
uv run streamlit run app.py

# Run demo
uv run python demo_matching.py --category IT

# Check progress
uv run python check_progress.py

# Validate
cd src/matching && uv run python auto_validate.py

# Complete pipeline
uv run python run_pipeline.py
```

### Important Files
- `app.py` - Main UI
- `data/processed/jobs_parsed.csv` - Processed jobs
- `data/processed/resume_skills.csv` - Processed resumes
- `logs/` - All system logs
- `QUICKSTART.md` - Quick reference guide

---

**Built with ❤️ for AI-powered career matching**

*Last Updated: March 6, 2026*
