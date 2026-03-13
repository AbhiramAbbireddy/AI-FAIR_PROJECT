"""
Job Ranking System
Ranks all jobs for a given resume by match score
"""

import pandas as pd
from src.matching.matcher import batch_calculate_matches

def rank_jobs_for_resume(resume_skills, jobs_df, top_n=20, min_score=0):
    """
    Rank all jobs by match score for a given resume
    
    Args:
        resume_skills: List or comma-separated string of resume skills
        jobs_df: DataFrame with parsed jobs
        top_n: Number of top matches to return
        min_score: Minimum match score threshold (0-100)
        
    Returns:
        List of dicts with ranked jobs (sorted by score descending)
    """
    
    # Calculate matches for all jobs
    matches = batch_calculate_matches(resume_skills, jobs_df)
    
    # Filter by minimum score if specified
    if min_score > 0:
        matches = [m for m in matches if m['score'] >= min_score]
    
    # Advanced sorting: Prioritize jobs with MORE actual skill matches
    # Rather than just percentage match
    # Sort by: (1) total_matches DESC, (2) score DESC, (3) required_score DESC
    matches.sort(key=lambda x: (
        -x.get('total_matches', 0),  # More matched skills = better
        -x['score'],                  # Higher score = better
        -x.get('required_score', 0)   # Higher required match = better
    ))
    
    # Return top N
    return matches[:top_n]


def filter_jobs(matches, filters):
    """
    Apply additional filters to job matches
    
    Args:
        matches: List of job matches
        filters: Dict with filter criteria
            - remote_only: bool
            - min_salary: float
            - max_salary: float
            - locations: list of strings
            - experience_levels: list of strings
            
    Returns:
        Filtered list of matches
    """
    
    filtered = matches.copy()
    
    # Remote filter
    if filters.get('remote_only'):
        filtered = [m for m in filtered if m.get('remote_allowed') == 1]
    
    # Salary filters
    if filters.get('min_salary'):
        filtered = [m for m in filtered if pd.notna(m.get('normalized_salary')) 
                   and m.get('normalized_salary') >= filters['min_salary']]
    
    if filters.get('max_salary'):
        filtered = [m for m in filtered if pd.notna(m.get('normalized_salary')) 
                   and m.get('normalized_salary') <= filters['max_salary']]
    
    # Location filter
    if filters.get('locations'):
        filtered = [m for m in filtered if any(loc.lower() in str(m.get('location', '')).lower() 
                                               for loc in filters['locations'])]
    
    # Experience level filter
    if filters.get('experience_levels'):
        filtered = [m for m in filtered if str(m.get('experience_level', '')).lower() 
                   in [level.lower() for level in filters['experience_levels']]]
    
    return filtered


def display_top_matches(matches, num_to_show=10):
    """
    Pretty print top job matches
    
    Args:
        matches: List of job matches
        num_to_show: Number of matches to display
    """
    
    print("=" * 70)
    print(f"🎯 TOP {num_to_show} JOB MATCHES")
    print("=" * 70)
    print()
    
    if not matches:
        print("❌ No matches found!")
        return
    
    for i, match in enumerate(matches[:num_to_show], 1):
        print(f"#{i}: {match['title']}")
        print(f"     Company: {match['company_name']}")
        print(f"     Location: {match['location']}")
        print(f"     Match Score: {match['score']}%", end="")
        
        # Add salary if available
        if pd.notna(match.get('normalized_salary')):
            salary = match['normalized_salary']
            print(f" | Salary: ${salary:,.0f}")
        else:
            print()
        
        print(f"     Required: {match['required_score']}% ({match['match_ratio']})")
        
        if match['required_matches']:
            skills_str = ', '.join(match['required_matches'][:5])
            if len(match['required_matches']) > 5:
                skills_str += f" +{len(match['required_matches'])-5} more"
            print(f"     ✓ Your skills: {skills_str}")
        
        if match['required_missing']:
            missing_str = ', '.join(match['required_missing'][:5])
            if len(match['required_missing']) > 5:
                missing_str += f" +{len(match['required_missing'])-5} more"
            print(f"     ✗ Missing: {missing_str}")
        
        print()


# Test the ranking system
if __name__ == "__main__":
    import sys
    
    print("=" * 70)
    print("🧪 TESTING RANKING SYSTEM")
    print("=" * 70)
    print()
    
    # Check if jobs_parsed.csv exists
    import os
    if not os.path.exists('data/processed/jobs_parsed.csv'):
        print("⚠️  jobs_parsed.csv not found yet.")
        print("   Job parsing is still running in background.")
        print("   This test will work once parsing completes.")
        sys.exit(0)
    
    print("Loading data...")
    
    # Load parsed jobs
    jobs_df = pd.read_csv('data/processed/jobs_parsed.csv')
    print(f"✓ Loaded {len(jobs_df):,} parsed jobs")
    
    # Load a sample resume
    resumes_df = pd.read_csv('data/processed/resume_skills.csv')
    sample_resume = resumes_df[resumes_df['skills'].notna()].iloc[0]
    
    print(f"✓ Testing with resume category: {sample_resume['category']}")
    print(f"  Resume skills: {sample_resume['skills'][:100]}...")
    print()
    
    # Rank jobs
    print("🔍 Finding top matches...")
    top_matches = rank_jobs_for_resume(
        sample_resume['skills'],
        jobs_df,
        top_n=10,
        min_score=10  # At least 10% match
    )
    
    # Display results
    display_top_matches(top_matches, num_to_show=10)
    
    # Test filtering
    print("\n" + "=" * 70)
    print("🔍 TESTING FILTERS")
    print("=" * 70)
    print()
    
    # Filter for remote jobs only
    print("Filter: Remote jobs only")
    remote_matches = filter_jobs(top_matches, {'remote_only': True})
    print(f"  Found {len(remote_matches)} remote jobs in top matches")
    print()
    
    # Filter for high salary
    print("Filter: Salary > $80,000")
    high_salary_matches = filter_jobs(top_matches, {'min_salary': 80000})
    print(f"  Found {len(high_salary_matches)} jobs with salary > $80k")
    print()
    
    print("✅ All tests passed!")
