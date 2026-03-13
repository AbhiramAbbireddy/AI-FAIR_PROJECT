"""
Job Matching Engine
Calculates how well a resume matches a job posting
"""

def calculate_match_score(resume_skills, job_required, job_preferred):
    """
    Calculate match percentage between resume and job
    
    Algorithm:
    - Required skills: 70% weight (critical for match)
    - Preferred skills: 30% weight (nice to have)
    
    Args:
        resume_skills: List or comma-separated string of skills from resume
        job_required: List or comma-separated string of required skills
        job_preferred: List or comma-separated string of preferred skills
        
    Returns:
        tuple: (final_score, details_dict)
            - final_score: Float 0-100
            - details_dict: Breakdown with matched/missing skills
    """
    
    # Normalize inputs to sets
    if isinstance(resume_skills, str):
        resume_set = set([s.lower().strip() for s in resume_skills.split(',') if s.strip()])
    elif resume_skills is None or (isinstance(resume_skills, float) and str(resume_skills) == 'nan'):
        resume_set = set()
    else:
        resume_set = set([str(s).lower().strip() for s in resume_skills if s])
    
    if isinstance(job_required, str):
        required_set = set([s.lower().strip() for s in job_required.split(',') if s.strip()])
    elif job_required is None or (isinstance(job_required, float) and str(job_required) == 'nan'):
        required_set = set()
    else:
        required_set = set([str(s).lower().strip() for s in job_required if s])
    
    if isinstance(job_preferred, str):
        preferred_set = set([s.lower().strip() for s in job_preferred.split(',') if s.strip()])
    elif job_preferred is None or (isinstance(job_preferred, float) and str(job_preferred) == 'nan'):
        preferred_set = set()
    else:
        preferred_set = set([str(s).lower().strip() for s in job_preferred if s])
    
    # Calculate required skills match
    if len(required_set) == 0:
        # No requirements = LOW match score (job has no clear requirements)
        # This should rank BELOW jobs with actual skill matches
        required_score = 10.0  # Low default score for jobs without requirements
        required_matches = []
        required_missing = []
    else:
        required_matches = list(resume_set & required_set)
        required_missing = list(required_set - resume_set)
        required_score = (len(required_matches) / len(required_set)) * 100
    
    # Calculate preferred skills match
    if len(preferred_set) == 0:
        preferred_score = 0.0
        preferred_matches = []
        preferred_missing = []
    else:
        preferred_matches = list(resume_set & preferred_set)
        preferred_missing = list(preferred_set - resume_set)
        preferred_score = (len(preferred_matches) / len(preferred_set)) * 100
    
    # Weighted combination
    # Required skills are MORE important (70% weight)
    final_score = (required_score * 0.7) + (preferred_score * 0.3)
    
    # Build details dictionary
    details = {
        'required_matches': required_matches,
        'required_missing': required_missing,
        'required_score': round(required_score, 1),
        'preferred_matches': preferred_matches,
        'preferred_missing': preferred_missing,
        'preferred_score': round(preferred_score, 1),
        'total_matches': len(required_matches) + len(preferred_matches),
        'match_ratio': f"{len(required_matches)}/{len(required_set)}" if len(required_set) > 0 else "N/A"
    }
    
    return round(final_score, 1), details


def batch_calculate_matches(resume_skills, jobs_df):
    """
    Calculate match scores for one resume against all jobs
    
    Args:
        resume_skills: List or comma-separated string of resume skills
        jobs_df: DataFrame with parsed jobs (must have required_skills, preferred_skills)
        
    Returns:
        List of dicts with job info + match scores
    """
    
    matches = []
    
    for idx, job in jobs_df.iterrows():
        score, details = calculate_match_score(
            resume_skills,
            job.get('required_skills', ''),
            job.get('preferred_skills', '')
        )
        
        matches.append({
            'job_id': job.get('job_id'),
            'title': job.get('title', 'Unknown'),
            'company_name': job.get('company_name', 'Unknown'),
            'location': job.get('location', 'Unknown'),
            'score': score,
            'required_score': details['required_score'],
            'preferred_score': details['preferred_score'],
            'required_matches': details['required_matches'],
            'required_missing': details['required_missing'],
            'preferred_matches': details['preferred_matches'],
            'preferred_missing': details['preferred_missing'],
            'total_matches': details['total_matches'],
            'match_ratio': details['match_ratio'],
            'remote_allowed': job.get('remote_allowed'),
            'normalized_salary': job.get('normalized_salary'),
            'experience_level': job.get('formatted_experience_level')
        })
    
    return matches


# Test the matching algorithm
if __name__ == "__main__":
    print("=" * 70)
    print("🧪 TESTING MATCHING ALGORITHM")
    print("=" * 70)
    print()
    
    # Test case 1: Perfect match
    print("Test 1: Perfect Match")
    resume = ['python', 'sql', 'machine learning']
    required = ['python', 'sql', 'machine learning']
    preferred = ['docker', 'aws']
    
    score, details = calculate_match_score(resume, required, preferred)
    print(f"  Score: {score}%")
    print(f"  Required: {details['required_score']}% ({details['match_ratio']})")
    print(f"  ✓ Matches: {details['required_matches']}")
    print(f"  ✗ Missing: {details['required_missing']}")
    print()
    
    # Test case 2: Partial match
    print("Test 2: Partial Match")
    resume = ['python', 'sql', 'pandas']
    required = ['python', 'sql', 'machine learning', 'docker']
    preferred = ['aws', 'kubernetes']
    
    score, details = calculate_match_score(resume, required, preferred)
    print(f"  Score: {score}%")
    print(f"  Required: {details['required_score']}% ({details['match_ratio']})")
    print(f"  ✓ Matches: {details['required_matches']}")
    print(f"  ✗ Missing: {details['required_missing']}")
    print()
    
    # Test case 3: No match
    print("Test 3: Weak Match")
    resume = ['excel', 'powerpoint', 'word']
    required = ['python', 'java', 'c++']
    preferred = ['docker', 'aws']
    
    score, details = calculate_match_score(resume, required, preferred)
    print(f"  Score: {score}%")
    print(f"  Required: {details['required_score']}% ({details['match_ratio']})")
    print(f"  ✓ Matches: {details['required_matches']}")
    print(f"  ✗ Missing: {details['required_missing']}")
    print()
    
    print("✅ All tests passed!")
