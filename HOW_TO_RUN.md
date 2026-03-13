# 🎯 FAIR-PATH: How to Run

Your project is now working with a **simplified, stable pipeline**:

```
Resume Upload → Skill Extraction → Role Matching
```

## ⚡ Quick Start

### Option 1: **Windows One-Click**
```bash
.venv\Scripts\Activate.ps1
python -m streamlit run app_minimal.py
```

### Option 2: **Test First (Recommended)**
```bash
.venv\Scripts\Activate.ps1
python test_pipeline.py
```

Then open your browser and navigate to the Streamlit URL (usually `http://localhost:8501`)

---

## 🎯 What the App Does

1. **Upload Resume** → PDF, DOCX, or TXT files
2. **Extract Skills** → Finds ~20-50 skills from your resume
3. **Match Roles** → Suggests 10+ suitable job roles
4. **Skill Breakdown** → Shows proficiency levels (Advanced/Intermediate/Basic)
5. **Gap Analysis** → Identifies missing skills for each role

---

## ✅ Pipeline Status

| Step | Status | Details |
|------|--------|---------|
| Text Extraction | ✅ | Supports PDF, DOCX, TXT |
| Skill Extraction | ✅ | Fast dictionary-based (30+ skills) |
| Role Matching | ✅ | 162 roles across 60 domains |
| Score Calculation | ✅ | Core (70%) + Optional (30%) skills |
| UI Display | ✅ | Clean Streamlit interface |

---

## 📊 Example Results

**Sample Resume:** Senior software engineer (8 years)  
**Extracted Skills:** 30 (Python, Docker, Kubernetes, AWS, SQL, etc.)  
**Top Matching Roles:**
1. Full Stack Developer - **71.0%** match
2. Site Reliability Engineer (SRE) - **65.0%** match
3. Backend Developer - **53.7%** match
4. DevOps Engineer - **53.7%** match
5. MLOps Engineer - **45.3%** match

---

## 🔧 Configuration

The app defaults to **fast dictionary-based skill extraction** (no heavy ML models).

To enable advanced RoBERTa NER extraction:
- Check "Use RoBERTa NER (slower)" in the sidebar
- First run will download the model (~800MB)
- Subsequent runs will be fast

---

## 📁 Key Files

- **`app_minimal.py`** ← Main Streamlit app (START HERE)
- **`test_pipeline.py`** ← Pipeline test script
- **`src/skill_extraction/extractor.py`** ← Skill extraction logic
- **`src/role_mapping/matcher.py`** ← Role matching algorithm
- **`src/role_mapping/role_database.py`** ← 162 roles across 60 domains

---

## 🚀 Next Steps

1. **Run the test:** `python test_pipeline.py`
2. **Launch the app:** `python -m streamlit run app_minimal.py`
3. **Upload your resume** and see matching roles
4. **Adjust settings:** Change min score, top N roles

---

## ❓ Troubleshooting

**Q: App won't start?**  
A: Run `python test_pipeline.py` first to verify the pipeline works

**Q: Skill extraction too slow?**  
A: Keep "Use RoBERTa NER" unchecked (default is fast dictionary matching)

**Q: Want to enable Sentence-BERT semantic matching?**  
A: Uncomment the semantic matching code in `app_minimal.py` (requires SBERT model)

**Q: Want to add more roles?**  
A: Edit `src/role_mapping/role_database.py` and add new roles to `COMPREHENSIVE_JOB_DATABASE`

---

**Version:** 2.0  
**Status:** ✅ Production Ready  
**Last Test:** ✅ PASSED
