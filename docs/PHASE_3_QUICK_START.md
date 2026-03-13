# 🚀 PHASE 3 QUICK START GUIDE

## 📋 WHAT YOU'LL BUILD THIS WEEK

A job matching engine that:
1. Reads job postings
2. Extracts required/preferred skills
3. Compares with resume skills
4. Calculates match scores (0-100%)
5. Ranks jobs by relevance

---

## 🎯 DELIVERABLES

At the end of Phase 3, you should have:
- ✅ `src/matching/parse_jobs.py` - Extracts skills from job descriptions
- ✅ `src/matching/matcher.py` - Calculates match scores
- ✅ `src/matching/ranker.py` - Ranks jobs for a resume
- ✅ `data/processed/jobs_parsed.csv` - Structured job database
- ✅ Test results showing 70%+ accuracy

---

## 📊 STEP-BY-STEP IMPLEMENTATION

### STEP 1: Explore Your Job Data (30 minutes)

```bash
# What job datasets do you have?
uv run python -c "
import pandas as pd
import os

# Check what's in jobs folder
job_files = []
for root, dirs, files in os.walk('data/raw/jobs'):
    for file in files:
        if file.endswith('.csv'):
            path = os.path.join(root, file)
            df = pd.read_csv(path, nrows=5)
            job_files.append({
                'file': path,
                'rows': len(df),
                'columns': list(df.columns)
            })
            print(f'\n--- {path} ---')
            print(f'Columns: {list(df.columns)}')
            print(f'Sample:\\n{df.head(2)}')
"
```

**Key Questions to Answer:**
- Which file has job descriptions?
- What column contains the description text?
- Are there separate columns for required/preferred skills?
- How many jobs total?

---

### STEP 2: Create Job Parser (2 hours)

Create: `src/matching/parse_jobs.py`

```python
"""
Job Description Parser
Extracts structured information from job postings
"""

import pandas as pd
import re
from src.skill_extraction.extract_resume_skills import dictionary_skill_match

def parse_job_description(job_text, skill_vocab):
    """
    Extract required and preferred skills from job description
    
    Args:
        job_text: Raw job description text
        skill_vocab: Set of all known skills
        
    Returns:
        dict with 'required' and 'preferred' skills
    """
    
    if pd.isna(job_text) or not job_text:
        return {'required': [], 'preferred': []}
    
    text_lower = str(job_text).lower()
    
    # Strategy 1: Look for explicit sections
    required_skills = []
    preferred_skills = []
    
    # Split text into sections
    sections = {
        'required': [],
        'preferred': []
    }
    
    # Pattern matching for "Required:", "Must have:", etc.
    required_patterns = [
        r'required skills?:(.+?)(?=preferred|qualifications|responsibilities|$)',
        r'must have:(.+?)(?=nice to have|preferred|$)',
        r'requirements:(.+?)(?=preferred|responsibilities|$)'
    ]
    
    preferred_patterns = [
        r'preferred:(.+?)(?=responsibilities|$)',
        r'nice to have:(.+?)(?=responsibilities|$)',
        r'bonus:(.+?)(?=responsibilities|$)'
    ]
    
    # Extract sections
    for pattern in required_patterns:
        match = re.search(pattern, text_lower, re.DOTALL | re.IGNORECASE)
        if match:
            sections['required'].append(match.group(1))
    
    for pattern in preferred_patterns:
        match = re.search(pattern, text_lower, re.DOTALL | re.IGNORECASE)
        if match:
            sections['preferred'].append(match.group(1))
    
    # Extract skills from each section
    if sections['required']:
        for section_text in sections['required']:
            skills = dictionary_skill_match(section_text, skill_vocab)
            required_skills.extend(skills)
    
    if sections['preferred']:
        for section_text in sections['preferred']:
            skills = dictionary_skill_match(section_text, skill_vocab)
            preferred_skills.extend(skills)
    
    # If no explicit sections found, extract all skills and mark as required
    if not required_skills and not preferred_skills:
        all_skills = dictionary_skill_match(text_lower, skill_vocab)
        required_skills = all_skills
    
    return {
        'required': list(set(required_skills)),
        'preferred': list(set(preferred_skills))
    }


def dictionary_skill_match(text, skill_vocab):
    """Match skills from vocabulary in text"""
    if pd.isna(text) or not text:
        return []
    
    text = str(text).lower()
    detected = []
    
    for skill in skill_vocab:
        pattern = r'\\b' + re.escape(skill) + r'\\b'
        if re.search(pattern, text):
            detected.append(skill)
    
    return detected


def process_all_jobs(jobs_csv_path, skill_vocab_path):
    """
    Process all job postings
    
    Args:
        jobs_csv_path: Path to job postings CSV
        skill_vocab_path: Path to skills vocabulary
        
    Returns:
        DataFrame with parsed jobs
    """
    
    print("Loading data...")
    jobs_df = pd.read_csv(jobs_csv_path)
    skill_vocab = set(pd.read_csv(skill_vocab_path)['skill'].str.lower())
    
    print(f"Processing {len(jobs_df)} jobs...")
    print(f"Using {len(skill_vocab)} skills in vocabulary")
    
    # Determine which column has description
    # Adapt this based on your data exploration in Step 1
    desc_column = 'description'  # CHANGE THIS to match your data
    
    if desc_column not in jobs_df.columns:
        print(f"ERROR: Column '{desc_column}' not found!")
        print(f"Available columns: {list(jobs_df.columns)}")
        return None
    
    results = []
    
    for idx, row in jobs_df.iterrows():
        description = row[desc_column]
        skills_data = parse_job_description(description, skill_vocab)
        
        results.append({
            'job_id': row.get('job_id', idx),
            'title': row.get('title', 'Unknown'),
            'company': row.get('company', 'Unknown'),
            'description': description,
            'required_skills': ', '.join(skills_data['required']),
            'preferred_skills': ', '.join(skills_data['preferred']),
            'required_count': len(skills_data['required']),
            'preferred_count': len(skills_data['preferred'])
        })
        
        if (idx + 1) % 1000 == 0:
            print(f"Processed {idx + 1}/{len(jobs_df)} jobs")
    
    parsed_df = pd.DataFrame(results)
    
    # Save
    output_path = 'data/processed/jobs_parsed.csv'
    parsed_df.to_csv(output_path, index=False)
    
    print(f"\\n✅ Saved to {output_path}")
    print(f"\\nStatistics:")
    print(f"  Jobs with required skills: {(parsed_df['required_count'] > 0).sum()}")
    print(f"  Jobs with preferred skills: {(parsed_df['preferred_count'] > 0).sum()}")
    print(f"  Avg required skills: {parsed_df['required_count'].mean():.1f}")
    print(f"  Avg preferred skills: {parsed_df['preferred_count'].mean():.1f}")
    
    return parsed_df


# Test on sample
if __name__ == "__main__":
    # TEST MODE: Process sample first
    skill_vocab = set(pd.read_csv('data/processed/skills_vocabulary.csv')['skill'].str.lower())
    
    sample_job = '''
    Data Scientist Position
    
    Required Skills:
    - Python programming
    - Machine learning
    - SQL
    - Statistics
    
    Preferred:
    - TensorFlow or PyTorch
    - AWS experience
    - PhD in related field
    
    Responsibilities: Build ML models...
    '''
    
    result = parse_job_description(sample_job, skill_vocab)
    print("Test Result:")
    print(f"Required: {result['required']}")
    print(f"Preferred: {result['preferred']}")
    
    # If test works, uncomment below to process all jobs:
    # process_all_jobs('data/raw/jobs/postings.csv', 'data/processed/skills_vocabulary.csv')
```

**How to run:**
```bash
uv run python src/matching/parse_jobs.py
```

---

### STEP 3: Build Matcher (1 hour)

Create: `src/matching/matcher.py`

```python
"""
Job Matching Engine
Calculates how well a resume matches a job
"""

def calculate_match_score(resume_skills, job_required, job_preferred):
    """
    Calculate match percentage
    
    Args:
        resume_skills: List of skills from resume
        job_required: List of required skills for job
        job_preferred: List of preferred skills for job
        
    Returns:
        (score, details_dict)
    """
    
    resume_set = set([s.lower().strip() for s in resume_skills if s])
    required_set = set([s.lower().strip() for s in job_required if s])
    preferred_set = set([s.lower().strip() for s in job_preferred if s])
    
    # Required skills matching
    if len(required_set) == 0:
        required_score = 100  # No requirements = automatic pass
    else:
        required_matches = resume_set & required_set
        required_score = (len(required_matches) / len(required_set)) * 100
    
    # Preferred skills matching
    if len(preferred_set) == 0:
        preferred_score = 0
    else:
        preferred_matches = resume_set & preferred_set
        preferred_score = (len(preferred_matches) / len(preferred_set)) * 100
    
    # Weighted combination (required matters more!)
    final_score = (required_score * 0.7) + (preferred_score * 0.3)
    
    # Details for explanation
    details = {
        'required_matches': list(resume_set & required_set),
        'required_missing': list(required_set - resume_set),
        'preferred_matches': list(resume_set & preferred_set),
        'preferred_missing': list(preferred_set - resume_set),
        'required_score': round(required_score, 1),
        'preferred_score': round(preferred_score, 1)
    }
    
    return round(final_score, 1), details


# Test
if __name__ == "__main__":
    # Test case
    resume = ['python', 'sql', 'machine learning', 'pandas', 'excel']
    required = ['python', 'sql', 'machine learning']
    preferred = ['tensorflow', 'docker', 'aws']
    
    score, details = calculate_match_score(resume, required, preferred)
    
    print(f"Match Score: {score}%\\n")
    print(f"Required Skills: {details['required_score']}%")
    print(f"  ✓ Have: {details['required_matches']}")
    print(f"  ✗ Missing: {details['required_missing']}")
    print(f"\\nPreferred Skills: {details['preferred_score']}%")
    print(f"  ✓ Have: {details['preferred_matches']}")
    print(f"  ✗ Missing: {details['preferred_missing']}")
```

---

### STEP 4: Build Ranker (1 hour)

Create: `src/matching/ranker.py`

```python
"""
Job Ranking System
Ranks all jobs for a given resume
"""

import pandas as pd
from src.matching.matcher import calculate_match_score

def rank_jobs_for_resume(resume_skills, jobs_df, top_n=20):
    """
    Rank all jobs by match score
    
    Args:
        resume_skills: List of skills from resume (or comma-separated string)
        jobs_df: DataFrame with parsed jobs
        top_n: Number of top matches to return
        
    Returns:
        List of dicts with job info + scores
    """
    
    # Handle string input
    if isinstance(resume_skills, str):
        resume_skills = [s.strip() for s in resume_skills.split(',')]
    
    matches = []
    
    for idx, job in jobs_df.iterrows():
        # Parse skills from stored strings
        required = [s.strip() for s in str(job['required_skills']).split(',') if s.strip()]
        preferred = [s.strip() for s in str(job['preferred_skills']).split(',') if s.strip()]
        
        # Calculate match
        score, details = calculate_match_score(resume_skills, required, preferred)
        
        matches.append({
            'job_id': job['job_id'],
            'title': job['title'],
            'company': job['company'],
            'score': score,
            'required_score': details['required_score'],
            'preferred_score': details['preferred_score'],
            'required_matches': details['required_matches'],
            'required_missing': details['required_missing'],
            'preferred_matches': details['preferred_matches'],
            'preferred_missing': details['preferred_missing']
        })
    
    # Sort by score (descending)
    matches.sort(key=lambda x: x['score'], reverse=True)
    
    return matches[:top_n]


# Test
if __name__ == "__main__":
    # Load data
    resume_df = pd.read_csv('data/processed/resume_skills.csv')
    jobs_df = pd.read_csv('data/processed/jobs_parsed.csv')
    
    # Test on first resume
    test_resume = resume_df.iloc[0]
    resume_skills = test_resume['skills']
    
    print(f"Testing resume: {test_resume['category']}")
    print(f"Resume skills: {resume_skills}\\n")
    
    # Get top 10 matches
    top_matches = rank_jobs_for_resume(resume_skills, jobs_df, top_n=10)
    
    print("\\n🎯 TOP 10 JOB MATCHES:\\n")
    for i, match in enumerate(top_matches, 1):
        print(f"#{i}: {match['title']} at {match['company']}")
        print(f"    Match: {match['score']}% (Required: {match['required_score']}%, Preferred: {match['preferred_score']}%)")
        print(f"    ✓ Matching: {', '.join(match['required_matches'][:5])}")
        print(f"    ✗ Missing: {', '.join(match['required_missing'][:5])}")
        print()
```

---

### STEP 5: Validate Results (1 hour)

Create: `src/matching/validate.py`

```python
"""
Validation: Manual check of matching quality
"""

import pandas as pd
from src.matching.ranker import rank_jobs_for_resume
import random

def validate_matching(n_samples=10):
    """
    Manually validate matching accuracy
    
    Process:
    1. Sample random resumes
    2. Get top 10 job matches
    3. Manually review if matches make sense
    4. Calculate precision@10
    """
    
    resume_df = pd.read_csv('data/processed/resume_skills.csv')
    jobs_df = pd.read_csv('data/processed/jobs_parsed.csv')
    
    # Sample random resumes
    sample_indices = random.sample(range(len(resume_df)), n_samples)
    
    print("MANUAL VALIDATION\\n")
    print("For each resume, review top 5 jobs and mark if they're good matches\\n")
    
    total_relevant = 0
    total_reviewed = 0
    
    for idx in sample_indices:
        resume = resume_df.iloc[idx]
        
        print("=" * 70)
        print(f"\\nRESUME #{idx}: {resume['category']}")
        print(f"Skills: {resume['skills']}\\n")
        
        matches = rank_jobs_for_resume(resume['skills'], jobs_df, top_n=5)
        
        print("TOP 5 MATCHES:\\n")
        for i, match in enumerate(matches, 1):
            print(f"  {i}. {match['title']} ({match['score']}%)")
            print(f"     Required matches: {', '.join(match['required_matches'][:3])}")
            print(f"     Missing: {', '.join(match['required_missing'][:3])}")
        
        print("\\n")
        relevant = input("How many of these 5 are actually good matches? (0-5): ")
        
        try:
            relevant_count = int(relevant)
            total_relevant += relevant_count
            total_reviewed += 5
        except:
            print("Invalid input, skipping...")
        
        print()
    
    precision = total_relevant / total_reviewed
    print("\\n" + "=" * 70)
    print(f"\\n📊 VALIDATION RESULTS")
    print(f"Precision@5: {precision:.1%}")
    print(f"Target: 75%+")
    print(f"Status: {'✅ PASS' if precision >= 0.75 else '❌ NEEDS IMPROVEMENT'}")


if __name__ == "__main__":
    validate_matching(n_samples=10)
```

---

## 🎯 SUCCESS CRITERIA

Phase 3 is complete when:

- [x] Job parser extracts skills from job descriptions
- [x] Matcher calculates reasonable scores (0-100%)
- [x] Ranker returns top N jobs sorted by score
- [x] Validation shows Precision@5 ≥ 75%
- [x] Code is clean and documented

---

## 🐛 COMMON ISSUES & SOLUTIONS

**Issue:** Jobs have no skills extracted
- **Cause:** Job descriptions don't have explicit "Required:" sections
- **Solution:** Fall back to extracting all skills from full description

**Issue:** All jobs have 100% match
- **Cause:** Job requirements empty → defaults to 100%
- **Solution:** Filter out jobs with no requirements

**Issue:** Precision@5 is low (< 70%)
- **Cause:** Skill matching too simplistic
- **Solution:** Add experience, education, location filters in Phase 3.5

---

## ⏱️ TIME ESTIMATE

- Step 1 (Explore data): 30 minutes
- Step 2 (Job parser): 2 hours
- Step 3 (Matcher): 1 hour
- Step 4 (Ranker): 1 hour
- Step 5 (Validation): 1 hour
- **Total:** ~6 hours (1-2 days)

---

## 📚 WHAT YOU'LL LEARN

1. **Information Extraction:** Pulling structured data from unstructured text
2. **Similarity Metrics:** Different ways to measure "how similar" two things are
3. **Ranking Algorithms:** Sorting by relevance (core of search engines!)
4. **Validation Methodology:** How to measure if your system works

---

## 🚀 READY TO START?

Wait for Phase 2 extraction to complete, then review the output:

```bash
# Check results
uv run python -c "
import pandas as pd
df = pd.read_csv('data/processed/resume_skills.csv')
print(f'Total resumes: {len(df)}')
print(f'Resumes with skills: {df[\"skills\"].notna().sum()}')
print(f'Average skills: {df[\"skills\"].str.count(\",\").add(1).mean():.1f}')
print(f'\\nSample:\\n{df[[\"category\", \"skills\"]].head()}')
"
```

If results look good → **START PHASE 3!**
