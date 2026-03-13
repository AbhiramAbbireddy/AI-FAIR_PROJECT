"""
Job Description Parser
Extracts structured skill requirements from job postings
Uses the same 288-skill vocabulary from resume extraction
"""

import pandas as pd
import re
from tqdm import tqdm

def dictionary_skill_match(text, skill_vocab):
    """
    Extract skills from text using word boundary matching
    
    Args:
        text: Job description text
        skill_vocab: Set of skill terms
        
    Returns:
        List of matched skills
    """
    if pd.isna(text) or not text:
        return []
    
    text = str(text).lower()
    detected = []
    
    for skill in skill_vocab:
        # Use word boundaries for accurate matching
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text):
            detected.append(skill)
    
    return detected


def parse_job_description(job_row, skill_vocab):
    """
    Extract required and preferred skills from a job posting
    
    Strategy:
    1. Look for explicit "Required:" and "Preferred:" sections
    2. If not found, mark all skills as required
    3. Extract from both description and skills_desc fields
    
    Args:
        job_row: DataFrame row with job data
        skill_vocab: Set of all known skills
        
    Returns:
        dict with 'required' and 'preferred' skill lists
    """
    
    # Combine description and skills_desc for comprehensive extraction
    description = str(job_row.get('description', ''))
    skills_desc = str(job_row.get('skills_desc', ''))
    
    full_text = description + " " + skills_desc
    full_text_lower = full_text.lower()
    
    if not full_text.strip() or full_text_lower == 'nan nan':
        return {'required': [], 'preferred': []}
    
    required_skills = []
    preferred_skills = []
    
    # Try to split into required vs preferred sections
    # Common patterns
    required_patterns = [
        r'required skills?[:\s]+(.+?)(?=preferred|qualifications|responsibilities|benefits|about|$)',
        r'must have[:\s]+(.+?)(?=nice to have|preferred|should have|$)',
        r'requirements?[:\s]+(.+?)(?=preferred|qualifications|responsibilities|nice to have|$)',
        r'qualifications?[:\s]+(.+?)(?=preferred|nice to have|responsibilities|$)'
    ]
    
    preferred_patterns = [
        r'preferred[:\s]+(.+?)(?=responsibilities|about|benefits|$)',
        r'nice to have[:\s]+(.+?)(?=responsibilities|about|benefits|$)',
        r'bonus[:\s]+(.+?)(?=responsibilities|about|benefits|$)',
        r'desired[:\s]+(.+?)(?=responsibilities|about|benefits|$)'
    ]
    
    # Extract required section
    required_section = ""
    for pattern in required_patterns:
        match = re.search(pattern, full_text_lower, re.DOTALL | re.IGNORECASE)
        if match:
            required_section = match.group(1)
            break
    
    # Extract preferred section
    preferred_section = ""
    for pattern in preferred_patterns:
        match = re.search(pattern, full_text_lower, re.DOTALL | re.IGNORECASE)
        if match:
            preferred_section = match.group(1)
            break
    
    # Extract skills from each section
    if required_section:
        required_skills = dictionary_skill_match(required_section, skill_vocab)
    
    if preferred_section:
        preferred_skills = dictionary_skill_match(preferred_section, skill_vocab)
    
    # If no explicit sections found, extract all skills as required
    if not required_skills and not preferred_skills:
        all_skills = dictionary_skill_match(full_text, skill_vocab)
        required_skills = all_skills
    
    return {
        'required': list(set(required_skills)),
        'preferred': list(set(preferred_skills))
    }


def process_jobs_batch(jobs_df, skill_vocab, sample_size=None, checkpoint_every=5000):
    """
    Process job postings to extract skill requirements
    
    Args:
        jobs_df: DataFrame with job postings
        skill_vocab: Set of skill terms
        sample_size: If provided, process only this many jobs (for testing)
        checkpoint_every: Save partial results every N jobs (default 5000)
        
    Returns:
        DataFrame with parsed job requirements
    """
    
    print("=" * 70)
    print("🎯 JOB DESCRIPTION PARSING")
    print("=" * 70)
    print()
    
    # Sample if requested
    if sample_size:
        print(f"⚠️  SAMPLE MODE: Processing {sample_size} jobs (testing)")
        jobs_df = jobs_df.head(sample_size).copy()
    else:
        print(f"📊 Processing ALL {len(jobs_df):,} jobs")
    
    print(f"📚 Using {len(skill_vocab)} skills in vocabulary")
    print(f"💾 Checkpointing every {checkpoint_every:,} jobs for real-time access")
    print()
    
    results = []
    output_path = 'data/processed/jobs_parsed.csv'
    
    print("⚙️  Extracting skills from job descriptions...")
    for idx, row in tqdm(jobs_df.iterrows(), total=len(jobs_df), desc="Processing jobs"):
        skills_data = parse_job_description(row, skill_vocab)
        
        results.append({
            'job_id': row['job_id'],
            'title': row.get('title', 'Unknown'),
            'company_name': row.get('company_name', 'Unknown'),
            'location': row.get('location', 'Unknown'),
            'description': row.get('description', ''),
            'required_skills': ', '.join(skills_data['required']),
            'preferred_skills': ', '.join(skills_data['preferred']),
            'required_count': len(skills_data['required']),
            'preferred_count': len(skills_data['preferred']),
            'total_skills': len(skills_data['required']) + len(skills_data['preferred']),
            'remote_allowed': row.get('remote_allowed', None),
            'normalized_salary': row.get('normalized_salary', None),
            'formatted_experience_level': row.get('formatted_experience_level', None),
            'work_type': row.get('work_type', None)
        })
        
        # Checkpoint: Save partial results for real-time access
        if len(results) % checkpoint_every == 0:
            partial_df = pd.DataFrame(results)
            partial_df.to_csv(output_path, index=False)
            # Don't print during processing to avoid cluttering progress bar
    
    parsed_df = pd.DataFrame(results)
    
    # Statistics
    print()
    print("=" * 70)
    print("✅ PARSING COMPLETE!")
    print("=" * 70)
    print()
    print(f"📊 Statistics:")
    print(f"  • Total jobs processed: {len(parsed_df):,}")
    print(f"  • Jobs with skills: {(parsed_df['total_skills'] > 0).sum():,} ({(parsed_df['total_skills'] > 0).sum()/len(parsed_df)*100:.1f}%)")
    print(f"  • Jobs with required skills: {(parsed_df['required_count'] > 0).sum():,}")
    print(f"  • Jobs with preferred skills: {(parsed_df['preferred_count'] > 0).sum():,}")
    print(f"  • Average required skills: {parsed_df['required_count'].mean():.1f}")
    print(f"  • Average preferred skills: {parsed_df['preferred_count'].mean():.1f}")
    print(f"  • Average total skills: {parsed_df['total_skills'].mean():.1f}")
    print()
    
    # Show sample
    print("📋 Sample Results:")
    for i in range(min(3, len(parsed_df))):
        job = parsed_df.iloc[i]
        print(f"\nJob {i+1}: {job['title']}")
        print(f"  Company: {job['company_name']}")
        print(f"  Required ({job['required_count']}): {job['required_skills'][:100]}...")
        if job['preferred_count'] > 0:
            print(f"  Preferred ({job['preferred_count']}): {job['preferred_skills'][:100]}...")
    
    return parsed_df


def main():
    """
    Main execution: Parse all job postings
    """
    
    print("Loading data...")
    
    # Load job postings
    jobs_df = pd.read_csv('data/raw/jobs/postings.csv')
    print(f"✓ Loaded {len(jobs_df):,} job postings")
    
    # Load skill vocabulary
    skill_vocab = set(pd.read_csv('data/processed/skills_vocabulary.csv')['skill'].str.lower())
    print(f"✓ Loaded {len(skill_vocab)} skills")
    print()
    
    # OPTION 1: Test on sample first (RECOMMENDED)
    # Uncomment to test on 1000 jobs first
    # parsed_df = process_jobs_batch(jobs_df, skill_vocab, sample_size=1000)
    
    # OPTION 2: Process ALL jobs (takes 20-30 minutes)
    # Uncomment to process full dataset
    parsed_df = process_jobs_batch(jobs_df, skill_vocab)
    
    # Save results
    output_path = 'data/processed/jobs_parsed.csv'
    parsed_df.to_csv(output_path, index=False)
    
    print()
    print(f"💾 Saved to: {output_path}")
    print()
    print("🎯 READY FOR MATCHING!")


if __name__ == "__main__":
    # Quick test mode
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        print("🧪 TEST MODE: Processing 100 jobs\n")
        jobs_df = pd.read_csv('data/raw/jobs/postings.csv')
        skill_vocab = set(pd.read_csv('data/processed/skills_vocabulary.csv')['skill'].str.lower())
        parsed_df = process_jobs_batch(jobs_df, skill_vocab, sample_size=100)
        print("\n✅ Test successful! Run without 'test' argument to process all jobs.")
    else:
        main()
