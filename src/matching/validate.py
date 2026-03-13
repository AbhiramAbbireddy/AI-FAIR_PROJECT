"""
Phase 3 Validation: Manual Accuracy Check
Randomly samples resumes and displays top job matches for manual review

Target: Precision@5 > 75% (at least 37.5/50 relevant matches)
"""

import pandas as pd
import numpy as np
from ranker import rank_jobs_for_resume, display_top_matches

def validate_matching_system(num_samples=10, top_k=5):
    """
    Sample random resumes, show top matches, collect manual judgments
    
    Args:
        num_samples: Number of resumes to test (default 10)
        top_k: Number of top jobs to evaluate per resume (default 5)
    """
    print("=" * 70)
    print("📋 PHASE 3 VALIDATION: MANUAL ACCURACY CHECK")
    print("=" * 70)
    print()
    print(f"Evaluating {num_samples} resumes × {top_k} jobs = {num_samples * top_k} judgments")
    print("Target: Precision@5 > 75% (at least {:.0f}/{} relevant)".format(
        num_samples * top_k * 0.75, num_samples * top_k
    ))
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
    np.random.seed(42)  # Reproducible
    sample_indices = np.random.choice(len(resumes_df), size=num_samples, replace=False)
    
    results = []
    
    for i, idx in enumerate(sample_indices, 1):
        resume = resumes_df.iloc[idx]
        
        print("=" * 70)
        print(f"📄 RESUME {i}/{num_samples}")
        print("=" * 70)
        print(f"Category: {resume['category']}")
        print(f"File: {resume['file_name']}")
        print(f"Skills: {resume['skills']}")
        print()
        
        # Get top matches
        top_matches = rank_jobs_for_resume(resume['skills'], jobs_df, top_n=top_k, min_score=0)
        
        # Display
        print(f"🔍 Top {top_k} Matches:")
        print()
        
        for j, match in enumerate(top_matches, 1):
            print(f"{j}. {match['title']}")
            print(f"   Company: {match.get('company', 'N/A')}")
            print(f"   Location: {match.get('location', 'N/A')}")
            print(f"   Match Score: {match['score']:.1f}%")
            print(f"   Required: {match['details']['required_percent']:.0f}% ({match['details']['required_matched']}/{match['details']['required_total']})")
            print(f"   Matched Skills: {', '.join(match['details']['matched_required']) if match['details']['matched_required'] else 'None'}")
            print()
        
        # Manual judgment
        print("-" * 70)
        print("❓ For each job above, is it RELEVANT for this resume?")
        print("   Relevant = Candidate could reasonably apply for this job")
        print()
        
        relevant_count = 0
        for j in range(1, top_k + 1):
            while True:
                answer = input(f"   Job {j} relevant? (y/n): ").lower().strip()
                if answer in ['y', 'n', 'yes', 'no']:
                    is_relevant = answer in ['y', 'yes']
                    relevant_count += is_relevant
                    break
                print("     Please enter 'y' or 'n'")
        
        precision = relevant_count / top_k
        print()
        print(f"✅ Resume {i} Precision@{top_k}: {precision:.1%} ({relevant_count}/{top_k} relevant)")
        print()
        
        results.append({
            'resume_idx': idx,
            'category': resume['category'],
            'relevant_count': relevant_count,
            'total': top_k,
            'precision': precision
        })
    
    # Overall results
    print()
    print("=" * 70)
    print("📊 VALIDATION RESULTS")
    print("=" * 70)
    print()
    
    total_relevant = sum(r['relevant_count'] for r in results)
    total_judgments = num_samples * top_k
    overall_precision = total_relevant / total_judgments
    
    print(f"Total relevant: {total_relevant}/{total_judgments}")
    print(f"Overall Precision@{top_k}: {overall_precision:.1%}")
    print()
    
    # Per-category breakdown
    print("Per-category results:")
    categories = {}
    for r in results:
        cat = r['category']
        if cat not in categories:
            categories[cat] = {'relevant': 0, 'total': 0}
        categories[cat]['relevant'] += r['relevant_count']
        categories[cat]['total'] += top_k
    
    for cat, stats in sorted(categories.items()):
        cat_precision = stats['relevant'] / stats['total']
        print(f"  {cat}: {cat_precision:.1%} ({stats['relevant']}/{stats['total']})")
    print()
    
    # Pass/fail
    target_precision = 0.75
    if overall_precision >= target_precision:
        print(f"✅ PASSED: {overall_precision:.1%} >= {target_precision:.0%} target")
        print("   Phase 3 matching system is validated!")
        print()
        print("🎯 Next step: Build Streamlit UI (Phase 4)")
    else:
        print(f"⚠️  BELOW TARGET: {overall_precision:.1%} < {target_precision:.0%}")
        print("   Consider:")
        print("   • Adjusting required/preferred weights (currently 70/30)")
        print("   • Improving skill extraction quality")
        print("   • Adding more skills to vocabulary")
    print()
    
    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv('data/processed/validation_results.csv', index=False)
    print("💾 Saved results to: data/processed/validation_results.csv")
    print()


if __name__ == "__main__":
    import sys
    
    # Parse arguments
    num_samples = 10
    top_k = 5
    
    if '--samples' in sys.argv:
        idx = sys.argv.index('--samples')
        num_samples = int(sys.argv[idx + 1])
    
    if '--top-k' in sys.argv:
        idx = sys.argv.index('--top-k')
        top_k = int(sys.argv[idx + 1])
    
    validate_matching_system(num_samples=num_samples, top_k=top_k)
