"""
Quick test of skill extraction on sample resumes
Tests the pipeline before running on full dataset
"""

import pandas as pd
from transformers import pipeline
import re
import warnings
warnings.filterwarnings('ignore')

print("🧪 TESTING SKILL EXTRACTION PIPELINE")
print("=" * 60)
print()

# Load sample data
print("📂 Loading data...")
df = pd.read_csv("data/processed/resumes_text.csv")
print(f"  ✓ Total resumes available: {len(df)}")

# Test on first 10 resumes only
test_df = df.head(10).copy()
print(f"  ✓ Testing on first {len(test_df)} resumes")
print()

skill_vocab = set(
    pd.read_csv("data/processed/skills_vocabulary.csv")["skill"].str.lower()
)
print(f"  ✓ Loaded {len(skill_vocab)} skills in vocabulary")
print()

# Try loading RoBERTa
print("🤖 Loading RoBERTa model...")
try:
    ner = pipeline(
        "token-classification",
        model="jjzha/jobbert_skill_extraction",
        aggregation_strategy="simple",
        device=-1
    )
    print("  ✅ Model loaded!")
    model_available = True
except Exception as e:
    print(f"  ⚠️  Model loading failed: {e}")
    print("  Will use dictionary matching only")
    model_available = False
print()

def dictionary_skill_match(text):
    if pd.isna(text) or not text:
        return []
    text = str(text).lower()
    detected = []
    for skill in skill_vocab:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text):
            detected.append(skill)
    return detected

def extract_skills(text):
    if pd.isna(text) or len(str(text).strip()) < 10:
        return []
    
    all_skills = []
    
    # Try RoBERTa if available
    if model_available:
        try:
            text_sample = str(text)[:5000]
            ner_results = ner(text_sample)
            for result in ner_results:
                token = result["word"].strip().lower().replace("##", "")
                if token in skill_vocab and len(token) >= 2:
                    all_skills.append(token)
        except:
            pass
    
    # Dictionary matching
    dict_skills = dictionary_skill_match(text)
    all_skills.extend(dict_skills)
    
    return sorted(list(set(all_skills)))

# Process test resumes
print("⚙️  Processing test resumes...")
for idx, row in test_df.iterrows():
    text = row["resume_text"]
    category = row["category"]
    
    skills = extract_skills(text)
    
    print(f"\n📄 Resume {idx+1}: {category}")
    print(f"  Text length: {len(str(text))} characters")
    print(f"  Skills found: {len(skills)}")
    if len(skills) > 0:
        print(f"  Skills: {', '.join(skills[:15])}")
        if len(skills) > 15:
            print(f"          ... and {len(skills)-15} more")
    else:
        print("  ⚠️  No skills found!")
        # Show first 200 chars to debug
        print(f"  Text preview: {str(text)[:200]}...")

print()
print("=" * 60)
print("✅ Test complete!")
print()
print("If results look good, run the full extraction:")
print("  python src\\skill_extraction\\extract_resume_skills.py")
