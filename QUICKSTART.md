# FAIR-PATH Quick Start Guide

## 🚀 Current Status
- **Phase 3:** Job parsing at 15% (ETA: ~1 hour)
- **Phase 4:** Streamlit UI ready to test

---

## ⚡ Quick Commands

### Test the System (After Parsing Completes)

```bash
# 1. Test matching demo
uv run python demo_matching.py

# 2. Test different categories
uv run python demo_matching.py --category IT
uv run python demo_matching.py --category ENGINEERING

# 3. Launch Streamlit UI
uv run streamlit run app.py
# OR use batch file:
launch_ui.bat
```

### Validate Accuracy

```bash
cd src/matching
uv run python validate.py
```

Target: **Precision@5 > 75%**

---

## 📂 Key Files

| File | Purpose |
|------|---------|
| `app.py` | Streamlit UI - full job matching interface |
| `demo_matching.py` | Command-line demo |
| `src/matching/parse_jobs.py` | Extract skills from job descriptions |
| `src/matching/matcher.py` | Calculate match scores |
| `src/matching/ranker.py` | Rank & filter jobs |
| `src/matching/validate.py` | Manual accuracy validation |

---

## 🎯 Next Steps

### When Parsing Completes (~1 hour):

1. **Run Demo**
   ```bash
   uv run python demo_matching.py --category IT
   ```

2. **Launch UI**
   ```bash
   uv run streamlit run app.py
   ```
   
3. **Validate** (10-15 minutes)
   ```bash
   cd src/matching
   uv run python validate.py
   ```

4. **If P@5 > 75%:** ✅ Phase 3 complete → Start Phase 5 (SHAP)

5. **If P@5 < 75%:** Tune algorithm weights

---

## 🖥️ Streamlit UI Features

- **Resume Selection:** Browse 2,484 resumes by category
- **Smart Matching:** Weighted algorithm (70% required, 30% preferred)
- **Filters:**
  - Match score threshold
  - Remote-only jobs
  - Salary range
  - Location
- **Results:**
  - Top N matches with scores
  - Skill breakdown (matched/missing)
  - Job details (salary, remote, experience)

---

## 📊 System Performance

| Metric | Value |
|--------|-------|
| Resumes processed | 2,484 (99.4% success) |
| Skills per resume | 8.1 average |
| Jobs to parse | 123,849 total |
| Jobs parsed so far | 18,276 (15%) |
| Skills vocabulary | 288 skills |
| Model | jjzha/jobbert_skill_extraction |

---

## 🔧 Troubleshooting

**Issue:** `jobs_parsed.csv not found`  
**Fix:** Wait for parsing to complete or check terminal progress

**Issue:** Streamlit not found  
**Fix:** `uv pip install streamlit`

**Issue:** Low match scores  
**Fix:** Adjust weights in `matcher.py` or expand skill vocabulary

---

## 📚 Documentation

- `docs/MENTOR_IMPLEMENTATION_GUIDE.md` - Full project guide
- `docs/PHASE_3_QUICK_START.md` - Phase 3 details
- `STATUS.md` - Real-time project status
