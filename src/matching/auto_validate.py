"""
Automated Validation System
Uses heuristics to automatically evaluate match quality
"""

import pandas as pd
import numpy as np
from ranker import rank_jobs_for_resume
import re

def automated_relevance_check(resume_category, job_title, job_description, matched_skills, match_score):
    """
    Automated relevance scoring using heuristics
    Returns: relevance score 0-1
    """
    relevance_score = 0.0
    
    # 1. Category-Job Title alignment (30%)
    category_keywords = {
        'INFORMATION-TECHNOLOGY': ['software', 'developer', 'engineer', 'programmer', 'it', 'tech', 'data', 'analyst'],
        'ENGINEERING': ['engineer', 'technical', 'design', 'mechanical', 'electrical', 'civil'],
        'HEALTHCARE': ['medical', 'nurse', 'doctor', 'health', 'clinical', 'patient'],
        'FINANCE': ['financial', 'accountant', 'analyst', 'banking', 'investment'],
        'SALES': ['sales', 'account', 'business development', 'representative'],
        'HR': ['human resource', 'hr', 'recruiter', 'talent'],
        'TEACHER': ['teacher', 'educator', 'instructor', 'professor', 'education'],
        'CONSULTANT': ['consultant', 'advisory', 'strategy'],
        'DESIGNER': ['designer', 'creative', 'ux', 'ui', 'graphic'],
        'DIGITAL-MEDIA': ['media', 'marketing', 'content', 'social', 'digital'],
    }
    
    job_lower = (job_title + ' ' + str(job_description)[:200]).lower()
    if resume_category in category_keywords:
        for keyword in category_keywords[resume_category]:
            if keyword in job_lower:
                relevance_score += 0.3
                break
    
    # 2. Match score contribution (40%)
    if match_score >= 70:
        relevance_score += 0.4
    elif match_score >= 40:
        relevance_score += 0.4 * (match_score / 70)
    
    # 3. Number of matched skills (30%)
    if len(matched_skills) >= 5:
        relevance_score += 0.3
    elif len(matched_skills) >= 3:
        relevance_score += 0.2
    elif len(matched_skills) >= 1:
        relevance_score += 0.1
    
    return min(relevance_score, 1.0)

def auto_validate_system(num_samples=100, sample_seed=42):
    """
    Automated validation using heuristic relevance scoring
    Much faster than manual validation
    """
    print("=" * 70)
    print("🤖 AUTOMATED VALIDATION SYSTEM")
    print("=" * 70)
    print()
    print(f"Testing {num_samples} random resume-job matches")
    print("Using heuristic relevance scoring (automated)")
    print()
    
    # Load data
    print("📂 Loading data...")
    jobs_df = pd.read_csv('data/processed/jobs_parsed.csv')
    resumes_df = pd.read_csv('data/processed/resume_skills.csv')
    resumes_df = resumes_df[resumes_df['skills'].notna()].reset_index(drop=True)
    
    print(f"  ✓ {len(jobs_df):,} jobs")
    print(f"  ✓ {len(resumes_df):,} resumes")
    print()
    
    # Random sample
    np.random.seed(sample_seed)
    sample_indices = np.random.choice(len(resumes_df), size=min(num_samples, len(resumes_df)), replace=False)
    
    results = []
    relevant_at_k = {1: 0, 3: 0, 5: 0, 10: 0}
    total_tests = len(sample_indices)
    
    print("🔍 Evaluating matches...")
    print()
    
    for i, idx in enumerate(sample_indices, 1):
        if i % 10 == 0:
            print(f"  Progress: {i}/{total_tests} ({i/total_tests*100:.0f}%)")
        
        resume = resumes_df.iloc[idx]
        
        # Get top 10 matches
        top_matches = rank_jobs_for_resume(resume['skills'], jobs_df, top_n=10, min_score=0)
        
        if not top_matches:
            continue
        
        # Evaluate top-k
        for k in [1, 3, 5, 10]:
            matches_at_k = top_matches[:k]
            relevant_count = 0
            
            for match in matches_at_k:
                matched_skills = match['details']['matched_required'] + match['details']['matched_preferred']
                relevance = automated_relevance_check(
                    resume['category'],
                    match['title'],
                    match.get('description', ''),
                    matched_skills,
                    match['score']
                )
                
                # Consider relevant if score >= 0.5
                if relevance >= 0.5:
                    relevant_count += 1
            
            if relevant_count > 0:
                relevant_at_k[k] += 1
        
        results.append({
            'resume_idx': idx,
            'category': resume['category'],
            'top_match_score': top_matches[0]['score'],
            'evaluated': True
        })
    
    print()
    print("=" * 70)
    print("📊 VALIDATION RESULTS")
    print("=" * 70)
    print()
    
    # Calculate metrics
    print("Success Rate @ K (at least 1 relevant in top K):")
    for k in [1, 3, 5, 10]:
        success_rate = (relevant_at_k[k] / total_tests) * 100
        status = "✅" if success_rate >= 75 else "⚠️" if success_rate >= 60 else "❌"
        print(f"  {status} Top-{k}: {success_rate:.1f}% ({relevant_at_k[k]}/{total_tests} resumes)")
    print()
    
    # Average top match score
    avg_top_score = sum(r['top_match_score'] for r in results) / len(results)
    print(f"Average Top Match Score: {avg_top_score:.1f}%")
    print()
    
    # Overall assessment
    if relevant_at_k[5] / total_tests >= 0.75:
        print("✅ SYSTEM VALIDATION: PASSED")
        print("   Matching quality meets target (75%+ success @ top-5)")
    elif relevant_at_k[5] / total_tests >= 0.60:
        print("⚠️ SYSTEM VALIDATION: ACCEPTABLE")
        print("   Matching quality is good but could be improved")
    else:
        print("❌ SYSTEM VALIDATION: NEEDS IMPROVEMENT")
        print("   Consider tuning weights or expanding skill vocabulary")
    print()
    
    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv('data/processed/auto_validation_results.csv', index=False)
    print("💾 Saved to: data/processed/auto_validation_results.csv")
    print()
    
    return relevant_at_k[5] / total_tests >= 0.75

if __name__ == "__main__":
    import sys
    
    num_samples = 100
    if len(sys.argv) > 1:
        num_samples = int(sys.argv[1])
    
    passed = auto_validate_system(num_samples=num_samples)
    
    if passed:
        print("🎯 Ready for Phase 5: SHAP Explainability")
    else:
        print("🔧 Recommend: Tune matcher.py weights or expand vocabulary")
