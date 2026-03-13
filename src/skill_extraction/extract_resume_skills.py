"""
Resume Skill Extraction using RoBERTa NER + Dictionary Matching
Hybrid approach for maximum coverage
"""

import pandas as pd
from transformers import pipeline
from tqdm import tqdm
import re
import warnings
warnings.filterwarnings('ignore')

print("=" * 70)
print("🎯 RESUME SKILL EXTRACTION PIPELINE")
print("=" * 70)
print()

# Load data
print("📂 Loading data...")
df = pd.read_csv("data/processed/resumes_text.csv")
print(f"  ✓ Loaded {len(df)} resumes")

skill_vocab = set(
    pd.read_csv("data/processed/skills_vocabulary.csv")["skill"].str.lower()
)
print(f"  ✓ Loaded {len(skill_vocab)} skills in vocabulary")
print()

# Initialize RoBERTa model
print("🤖 Loading RoBERTa model (jjzha/jobbert_skill_extraction)...")
print("  ⏳ This may take a minute on first run (downloading model)...")
try:
    ner = pipeline(
        "token-classification",
        model="jjzha/jobbert_skill_extraction",
        aggregation_strategy="simple",
        device=-1  # Use CPU
    )
    print("  ✅ RoBERTa model loaded successfully!")
    model_available = True
except Exception as e:
    print(f"  ⚠️  Warning: Could not load RoBERTa model - {e}")
    print("  📝 Will use dictionary matching only")
    model_available = False
print()

def dictionary_skill_match(text):
    """
    Extract skills using dictionary matching with fuzzy boundaries
    More sophisticated than simple substring search
    """
    if pd.isna(text) or not text:
        return []
    
    text = str(text).lower()
    detected = []
    
    for skill in skill_vocab:
        # Use word boundaries for better matching
        # This prevents "java" from matching "javascript"
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text):
            detected.append(skill)
    
    return detected


def extract_skills_from_resume(text, use_ner=True):
    """
    Extract skills from resume text using hybrid approach:
    1. RoBERTa NER (if available)
    2. Dictionary matching (always)
    """
    if pd.isna(text) or not text or len(str(text).strip()) < 10:
        return []
    
    text = str(text)
    all_skills = []
    
    # Method 1: RoBERTa NER
    if use_ner and model_available:
        try:
            # Truncate text if too long (RoBERTa has token limits)
            max_length = 5000  # characters
            if len(text) > max_length:
                text_sample = text[:max_length]
            else:
                text_sample = text
            
            ner_results = ner(text_sample)
            
            for result in ner_results:
                token = result["word"].strip().lower()
                # Clean up RoBERTa output (removes ## artifacts)
                token = token.replace("##", "")
                
                if token in skill_vocab and len(token) >= 2:
                    all_skills.append(token)
        
        except Exception as e:
            # Skip this resume if NER fails
            pass
    
    # Method 2: Dictionary matching (on full text)
    dict_skills = dictionary_skill_match(text)
    all_skills.extend(dict_skills)
    
    # Deduplicate and sort
    unique_skills = sorted(list(set(all_skills)))
    
    return unique_skills


# Test on sample first
print("🧪 Testing on sample resume...")
sample_text = df["resume_text"].iloc[0] if len(df) > 0 else ""
sample_skills = extract_skills_from_resume(sample_text, use_ner=model_available)
print(f"  ✓ Sample extraction works! Found {len(sample_skills)} skills")
if len(sample_skills) > 0:
    print(f"  📋 Sample: {', '.join(sample_skills[:10])}")
print()

# Process all resumes
print(f"⚙️  Processing {len(df)} resumes...")
print("  (This will take several minutes...)")
print()

all_skills = []

for idx, text in enumerate(tqdm(df["resume_text"], desc="Extracting skills")):
    skills = extract_skills_from_resume(text, use_ner=model_available)
    all_skills.append(", ".join(skills))
    
    # Show progress every 500 resumes
    if (idx + 1) % 500 == 0:
        avg_skills = sum([len(s.split(", ")) if s else 0 for s in all_skills]) / len(all_skills)
        print(f"  📊 Progress: {idx+1}/{len(df)} | Avg {avg_skills:.1f} skills/resume")

df["skills"] = all_skills

# Save results
print()
print("💾 Saving results...")
df.to_csv("data/processed/resume_skills.csv", index=False)

# Statistics
print()
print("=" * 70)
print("✅ EXTRACTION COMPLETE!")
print("=" * 70)

total_skills_found = sum([len(s.split(", ")) if s else 0 for s in all_skills])
resumes_with_skills = sum([1 for s in all_skills if s])

print(f"""
📊 Statistics:
  • Total resumes processed: {len(df)}
  • Resumes with skills found: {resumes_with_skills} ({resumes_with_skills/len(df)*100:.1f}%)
  • Total skills extracted: {total_skills_found}
  • Average skills per resume: {total_skills_found/len(df):.1f}
  • Method used: {'RoBERTa NER + Dictionary' if model_available else 'Dictionary only'}
  
💾 Saved to: data/processed/resume_skills.csv
""")