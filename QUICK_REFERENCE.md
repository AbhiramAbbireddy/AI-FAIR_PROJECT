# 🎯 FAIR-PATH Quick Reference Card

## 🚀 Launch Dashboard (30 seconds)

```bash
# Activate environment
.venv\Scripts\Activate.ps1

# Run app
python -m streamlit run app_enhanced.py
```

**Opens at:** http://localhost:8501

---

## 📦 All 5 Features Included

| # | Feature | What It Does | Test Command |
|---|---------|-------------|---|
| 1 | **Skill Extraction** | Extracts skills from resume | `python test_all_features.py` |
| 2 | **Role Matching** | Matches 162 roles (70% core + 30% optional) | ↓ |
| 3 | **Skill Gaps** | Ranks missing high-demand skills | ↓ |
| 4 | **Market Trends** | Shows growing/declining skills | ↓ |
| 5 | **Explainability** | Explains why roles match | ↓ |

---

## 🎯 App Tabs (5 Total)

```
1. 🔍 SKILLS          → Extracted skills by proficiency
2. 🎯 SUITABLE ROLES  → Top 10 matching roles with scores
3. 📊 SKILL GAPS      → Missing high-demand skills (prioritized)
4. 📈 TRENDS          → Growing and declining market skills
5. 💡 EXPLAINABILITY  → Why each role matches (score breakdown)
```

---

## ⚙️ Sidebar Settings

```
┌─────────────────────────────────────┐
│ Upload Resume (PDF/DOCX/TXT)        │
├─────────────────────────────────────┤
│ ☐ Use RoBERTa NER (slower)         │
│ [Slider] Top N roles: 1 ---- 20 [10]│
│ [Slider] Min score: 0 ---- 80% [10] │
│ [Button] 🚀 Analyze Resume         │
└─────────────────────────────────────┘
```

---

## 📊 Example Output

### Input
```
Senior Full-Stack Engineer Resume (27 skills)
```

### Output Summary
```
Skills Extracted:    27 skills
Matching Roles:      10 roles found
Top Match:           Full Stack Developer (71.0%)
High-Skill Gaps:     Testing, Problem Solving
Trending Up:         Kubernetes, Docker, Kafka
Most In-Demand:      Origin, Science, Problem Solving
```

---

## 🧪 Testing Commands

```bash
# Quick test (1-2 minutes)
python test_pipeline.py

# Full feature test (2-3 minutes)
python test_all_features.py

# Launch app
python -m streamlit run app_enhanced.py
```

---

## 📁 Key Files

```
ROOT/
├── app_enhanced.py           ← Main Streamlit app (START HERE)
├── test_all_features.py      ← Test all 5 features
├── test_pipeline.py          ← Quick pipeline test
│
├── src/
│   ├── skill_extraction/     ← Skill extraction module
│   ├── role_mapping/         ← 162 roles database + matcher
│   ├── skill_gap/            ← Gap ranking
│   ├── forecasting/          ← Trend analysis
│   ├── explainability/       ← SHAP explainability
│   ├── fairness/             ← Bias detection (optional)
│   └── api/                  ← FastAPI backend
│
└── data/processed/
    ├── jobs_parsed.csv       ← Job data for gaps/trends
    ├── skills_vocabulary.csv ← Canonical skill names
    └── ...
```

---

## 🎯 Feature Details

### 1️⃣ Skill Extraction
- Input: Resume text (PDF/DOCX/TXT)
- Output: ~30 skills with proficiency levels
- Methods: Dictionary + optional RoBERTa NER

### 2️⃣ Role Matching
- Database: **162 roles** across **60 domains**
- Algorithm: Core×70% + Optional×30%
- Score: 0-100% match percentage
- Output: Top N ranked roles

### 3️⃣ Skill Gaps
- Identifies: Missing market-demanded skills
- Priority: High (≥15%), Medium (5-15%), Low (<5%)
- Data: Analyzed across 2000+ job postings
- Output: Top 15 gaps ranked by priority

### 4️⃣ Market Trends
- Analyzes: 2000+ job postings
- Calculates: Skill frequency % and growth rates
- Identifies: Top 50 trending skills
- Shows: Growing vs declining skills

### 5️⃣ Explainability
- Explains: Why each score is calculated
- Method: Transparent feature breakdown
- Shows: Core/optional coverage percentages
- Not: Black-box ML decision

---

## 🔢 Performance

```
Skill Extraction:     ~1 second
Role Matching:        <1 second
Skill Gaps:           <1 second
Trends:               <2 seconds
Explainability:       <1 second
─────────────────────────────
TOTAL:               ~5-10 seconds
```

---

## ✅ What Works

- ✅ PDF, DOCX, TXT upload
- ✅ Skill extraction
- ✅ Role matching (162 roles)
- ✅ Skill priority ranking
- ✅ Market trend analysis
- ✅ Score explanations
- ✅ Responsive UI
- ✅ All 5 features integrated

---

## ❓ Quick FAQ

**Q: Is NER required?**  
A: No. Default (fast) uses dictionary. RoBERTa NER is optional.

**Q: How many roles?**  
A: 162 roles across 60 domains (Software, AI/ML, Data, Electrical, Mechanical, Civil, Aerospace, etc.)

**Q: How are scores calculated?**  
A: `Score = (Core% × 0.70) + (Optional% × 0.30)`

**Q: Can I adjust settings?**  
A: Yes. Use sidebar sliders: Min Score (0-80%) and Top N Roles (3-20).

**Q: Is the scoring explainable?**  
A: Yes. Full transparency in "Explainability" tab showing all matched skills.

**Q: How long does it take?**  
A: ~5-10 seconds total from upload to results.

---

## 🚀 Three Ways to Use

### Way 1: Quick Test
```bash
python test_all_features.py
# See all features working
```

### Way 2: Full App
```bash
python -m streamlit run app_enhanced.py
# Interactive dashboard with UI
```

### Way 3: API
```bash
# Launch FastAPI backend
python -m uvicorn src.api.routes:app
# Use REST endpoints
```

---

## 📞 Need Help?

1. Read: `COMPLETE_GUIDE.md` (full documentation)
2. Read: `FEATURE_INVENTORY.md` (all features listed)
3. Run: `test_all_features.py` (see expected output)
4. Launch: `app_enhanced.py` (interactive testing)

---

**Status:** ✅ Production Ready | **Version:** 2.1 | **Features:** 5/5 ✅
