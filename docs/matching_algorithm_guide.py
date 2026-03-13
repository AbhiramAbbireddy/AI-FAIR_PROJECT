"""
Job Matching Algorithm - Core Logic
This is what you'll implement in Phase 3

Key Concept: Calculate similarity between resume skills and job requirements
"""

def calculate_match_score(resume_skills, job_requirements):
    """
    Real-world matching algorithm used in production systems
    
    Args:
        resume_skills: List of skills from resume
        job_requirements: Dict with 'required' and 'preferred' skills
        
    Returns:
        match_score: Float between 0-100
        details: Dict with breakdown
    """
    
    required_skills = set(job_requirements['required'])
    preferred_skills = set(job_requirements.get('preferred', []))
    user_skills = set(resume_skills)
    
    # Core matching logic
    required_matches = user_skills & required_skills
    preferred_matches = user_skills & preferred_skills
    
    # Scoring (industry standard weights)
    if len(required_skills) == 0:
        required_score = 100  # No requirements = default match
    else:
        required_score = (len(required_matches) / len(required_skills)) * 100
    
    if len(preferred_skills) == 0:
        preferred_score = 0
    else:
        preferred_score = (len(preferred_matches) / len(preferred_skills)) * 100
    
    # Weighted combination (required skills matter MORE)
    final_score = (required_score * 0.7) + (preferred_score * 0.3)
    
    details = {
        'required_matches': list(required_matches),
        'required_missing': list(required_skills - user_skills),
        'preferred_matches': list(preferred_matches),
        'preferred_missing': list(preferred_skills - user_skills),
        'required_score': round(required_score, 1),
        'preferred_score': round(preferred_score, 1)
    }
    
    return round(final_score, 1), details


# Example usage
if __name__ == "__main__":
    # Test case
    resume_skills = ['python', 'sql', 'machine learning', 'pandas', 'excel']
    
    job_requirements = {
        'required': ['python', 'sql', 'machine learning'],
        'preferred': ['tensorflow', 'docker', 'aws']
    }
    
    score, details = calculate_match_score(resume_skills, job_requirements)
    
    print(f"Match Score: {score}%")
    print(f"\nRequired Skills Match: {details['required_score']}%")
    print(f"  ✓ Have: {details['required_matches']}")
    print(f"  ✗ Missing: {details['required_missing']}")
    print(f"\nPreferred Skills Match: {details['preferred_score']}%")
    print(f"  ✓ Have: {details['preferred_matches']}")
    print(f"  ✗ Missing: {details['preferred_missing']}")
```
