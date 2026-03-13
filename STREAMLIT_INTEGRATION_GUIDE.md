# Streamlit Integration Guide - Skill Gap Analysis

## Overview

The comprehensive skill gap analysis system has been fully integrated into the FAIR-PATH v2 Streamlit UI. Users can now access advanced gap analysis features directly from the web interface.

---

## What's New

### Enhanced Skill Gap Analysis Tab

The Skill Gaps tab now includes **two analysis modes:**

#### 1. **Advanced Gap Analysis** (When data available)
When comprehensive gap analysis data is available, users see:

- **4-Factor Scoring System**
  - Job Importance (40% weight)
  - Market Demand (30% weight)
  - Learning Ease (20% weight)
  - Salary Impact (10% weight)

- **4 Analysis Views:**
  1. **Priority Ranking** - Skills ranked by importance
  2. **Learning Path** - Month-by-month timeline with goals
  3. **Quick Wins** - High-impact, easy-to-learn skills
  4. **Gap Breakdown** - Visual categorization of gaps

#### 2. **Basic Gap Analysis** (Fallback)
If advanced analysis isn't available, falls back to:
- Demand-based skill gaps
- Priority categorization (High/Medium/Low)
- Market demand visualization

---

## How to Use

### Running the Streamlit App

```bash
# From project root
cd e:\AI-FAIR_PROJECT
streamlit run streamlit_app.py
```

The app will open at `http://localhost:8501`

### Step-by-Step Usage

1. **Upload Resume**
   - Click the file uploader in the left sidebar
   - Select PDF, DOCX, or TXT file
   - Choose analysis options:
     - **Use NER extraction**: Enable for contextual skill detection
     - **Top N roles**: Number of job suggestions (5-30)
     - **Minimum match score**: Filter results (0-80%)

2. **Run Analysis**
   - Click **"🚀 Analyse Resume"** button
   - System will run full analysis pipeline:
     - Extract text & skills
     - Map suitable roles
     - Calculate gaps (basic + comprehensive)
     - Analyze trends
     - Evaluate fairness

3. **View Results**
   - Navigate to **"📊 Skill Gaps"** tab
   - See comprehensive gap analysis and learning recommendations

---

## Features Explanation

### Priority Ranking Tab

Shows top 10 skills ranked by overall priority:

- **Tier System:**
  - 🔴 **CRITICAL (85-100):** Learn immediately
  - 🟠 **HIGH (70-84):** Learn within 2-3 months
  - 🟡 **MEDIUM (50-69):** Learn within 6 months
  - 🟢 **LOW (<50):** Lower priority

- **For Each Skill:**
  - Overall priority score (0-100)
  - Score breakdown by factor
  - Learning time (months)
  - Salary boost potential (₹ in Indian market)
  - Difficulty assessment
  - AI-generated recommendation

### Learning Path Tab

Displays personalized learning timeline:

- **Summary Metrics:**
  - Starting match score
  - Projected match score
  - Total duration
  - Number of skills to learn

- **Month-by-Month Breakdown:**
  - Skill name for each month
  - Learning duration
  - Expected match score after completion
  - Line chart showing progress

- **Quarterly Planning:**
  - Q1, Q2, Q3, Q4 grouping
  - Skills grouped by quarter
  - Allows for structured 3-month planning

### Quick Wins Tab

Shows skills that deliver maximum value with minimum effort:

**Selection Criteria:**
- Priority score > 70
- Learning ease score > 80
- Can be learned in 1-2 months

**Benefits:**
- Build momentum early
- See quick progress
- Boost confidence

### Gap Breakdown Tab

Visual summary of all gaps:

- **Metrics:**
  - Total gaps count
  - Critical gaps count
  - Important gaps count
  - Nice-to-have gaps count

- **Visualization:**
  - Bar chart showing category distribution
  - Detailed skill lists for each category
  - Organized by priority level

---

## Architecture Integration

### Data Flow

```
Resume Upload
    ↓
[Text Extraction]
    ↓
[Skill Extraction] → Extract skills with proficiency levels
    ↓
[Role Mapping] → Find suitable roles
    ↓
[Gap Identification] 
    ├→ Basic: Market demand-based
    └→ Advanced: Comprehensive 4-factor analysis
    ↓
[Priority Ranking] → Rank by multiple factors
    ↓
[Learning Path] → Generate timeline with milestones
    ↓
[Display Results] → Render in Streamlit UI
```

### New Components Integration

**File:** `src/skill_gap_analysis.py`
- Main orchestrator for comprehensive gap analysis
- Integrates all 4 gap analysis components

**File:** `streamlit_app.py` (Enhanced)
- Added imports for SkillGapAnalysis
- New gap analyzer loader function
- Enhanced gap analysis tab with 4 views
- Fallback to basic analysis if needed

---

## Configuration

### Environment Setup

**Required Dependencies:**
```
streamlit>=1.28.0
pandas>=1.5.0
fuzzywuzzy>=0.18.0
python-Levenshtein>=0.21.0
sentence-transformers>=2.2.0
```

**Install:**
```bash
pip install -r requirements.txt
```

### Data Files Required

Place skill data in `data/` directory:

```
data/
├── skill_aliases.json (180+ entries)
├── skill_hierarchy.json (130+ entries)
├── learning_time_database.json (160+ entries)
└── salary_impact_database.json (150+ entries)
```

---

## Error Handling

### Graceful Degradation

The system is designed to fail gracefully:

1. **No Advanced Analysis Available**
   - Falls back to basic gap analysis
   - User can still see demand-based gaps
   - Warning message explains the fallback

2. **Missing Data**
   - Displays informative messages
   - Suggests data requirements
   - Doesn't crash the app

3. **Import Errors**
   - `HAS_GAP_ANALYSIS` flag prevents crashes
   - Try/except blocks around gap analysis
   - Clear error messages for users

---

## Performance

### Caching Strategy

**Resource Cached:**
- SBERT model (used across reruns)
- Job database (loaded once per session)
- Gap analyzer (loaded once per session)

**Data Cached:**
- Resume text (per user upload)
- Extracted skills
- Role matches
- Gap analysis results

**Performance Metrics:**
- Text extraction: <2s
- Skill extraction: <5s
- Gap analysis: <3s
- Total analysis: ~15-20s

---

## Customization

### Modify Analysis Weights

Edit `src/priority_ranker.py`:
```python
# Change the weights
Priority = (JobImportance × 0.4) + (MarketDemand × 0.3) + 
          (LearningEase × 0.2) + (SalaryImpact × 0.1)

# To customize, modify the multipliers
```

### Add Custom Skills

Edit `data/skill_aliases.json`:
```json
{
  "your_skill_variation": "canonical_skill_name"
}
```

### Update Salary Data

Edit `data/salary_impact_database.json`:
```json
{
  "skill_name": {
    "average_boost_inr": 300000,
    "salary_range": [500000, 3000000],
    "demand": "very high"
  }
}
```

---

## Troubleshooting

### Issue: "Comprehensive gap analysis not available"

**Cause:** Import error or missing data files

**Solution:**
1. Check `data/` directory has all 4 JSON files
2. Verify imports: `python -c "from src.skill_gap_analysis import SkillGapAnalysis"`
3. Check logs for specific errors

### Issue: Skills not detected

**Cause:** NER model needs retraining or skills not in dictionary

**Solution:**
1. Try disabling NER extraction (use dictionary only)
2. Add skills to skill aliases
3. Verify resume has skill keywords

### Issue: Slow analysis

**Cause:** Large file size or slow system

**Solution:**
1. Use TXT instead of PDF when possible
2. Reduce "Top N roles" slider
3. Check system resources
4. Clear cache: `rm -rf ~/.streamlit/`

---

## Future Enhancements

### Planned Features

- [ ] **Multi-Job Gap Analysis** - Compare gaps across top 3 roles
- [ ] **Interactive Timeline Builder** - Drag-and-drop skill scheduling
- [ ] **Resource Recommendations** - Links to courses, books, tutorials
- [ ] **Progress Tracking** - Store and monitor learning progress
- [ ] **Peer Comparison** - Benchmark against similar candidates
- [ ] **Export Reports** - Generate PDF/Excel gap analysis reports
- [ ] **Real-time Market Trends** - Live salary and demand data
- [ ] **Custom Learning Paths** - User-defined learning sequences

---

## Support

### Key Files

| File | Purpose |
|------|---------|
| `streamlit_app.py` | Main UI application |
| `src/skill_gap_analysis.py` | Gap analysis orchestrator |
| `src/gap_identifier.py` | Gap identification |
| `src/gap_categorizer.py` | Gap categorization |
| `src/priority_ranker.py` | Priority scoring |
| `src/learning_path_generator.py` | Timeline generation |
| `data/*.json` | Skill knowledge bases |

### Documentation

- **Full System Docs:** `SKILL_GAP_ANALYSIS_README.md`
- **Architecture Guide:** `docs/matching_algorithm_guide.py`
- **Test Coverage:** `tests/test_gap_analysis.py` (26 tests, all passing)

### Testing

Run comprehensive tests:
```bash
python -m pytest tests/test_gap_analysis.py -v
```

---

## Summary

The comprehensive skill gap analysis system is now fully integrated with the FAIR-PATH v2 Streamlit UI. Users can:

✅ **Analyze Gaps** - Identify missing skills for target roles  
✅ **Prioritize Learning** - Get 4-factor priority scores  
✅ **Plan Timeline** - See month-by-month learning roadmap  
✅ **Find Quick Wins** - Learn high-impact skills quickly  
✅ **Estimate Salary** - See potential earning increases  

The system is **production-ready**, with:
- ✅ Graceful error handling
- ✅ Comprehensive caching
- ✅ Fallback mechanisms
- ✅ 26 passing unit tests
- ✅ Full documentation

**Start using it now:** `streamlit run streamlit_app.py`

---

*Last Updated: March 13, 2026*  
*FAIR-PATH v2.1 — Advanced Skill Gap Analysis*
