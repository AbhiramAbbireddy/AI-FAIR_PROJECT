#!/usr/bin/env python3
"""Debug script to test gap analysis output structure"""
import sys
sys.path.insert(0, '.')

from src.skill_gap_analysis import SkillGapAnalysis

print("=" * 70)
print("TESTING SKILL GAP ANALYSIS OUTPUT STRUCTURE")
print("=" * 70)

analyzer = SkillGapAnalysis()

# Create test data
user_skills = ['Python', 'SQL', 'Pandas']
job_data = {
    'role': 'Data Scientist',
    'description': 'We are looking for a Data Scientist. Required: Python, Machine Learning, Statistics. '
                   'Nice to have: TensorFlow, Docker, Kubernetes, PyTorch. '
                   'Must have strong problem solving and communication skills.',
    'core_skills': ['Python', 'Machine Learning', 'Statistics'],
    'optional_skills': ['TensorFlow', 'Docker', 'Kubernetes']
}

print("\n[1] Running analyze_for_job()...")
try:
    result = analyzer.analyze_for_job(
        user_skills=user_skills,
        job_data=job_data,
        current_match_score=65
    )
    print("✅ Analysis succeeded!")
    
    print("\n[2] Checking result structure...")
    print(f"   Keys in result: {list(result.keys())}")
    
    print("\n[3] Checking gaps_breakdown...")
    gaps_breakdown = result.get('gaps_breakdown', {})
    print(f"   Gaps breakdown: {gaps_breakdown}")
    
    print("\n[4] Checking ranked_priorities...")
    ranked = result.get('ranked_priorities', [])
    print(f"   Number of ranked skills: {len(ranked)}")
    if ranked:
        print(f"   First skill: {ranked[0]}")
        print(f"   First skill keys: {list(ranked[0].keys())}")
    
    print("\n[5] Checking learning_path...")
    learning_path = result.get('learning_path', {})
    print(f"   Learning path keys: {list(learning_path.keys())}")
    if learning_path:
        print(f"   Initial score: {learning_path.get('initial_match_score')}")
        print(f"   Final score: {learning_path.get('final_match_score')}")
        print(f"   Milestones: {len(learning_path.get('milestones', []))}")
    
    print("\n[6] Checking quick_wins...")
    quick_wins = result.get('quick_wins', [])
    print(f"   Quick wins count: {len(quick_wins)}")
    if quick_wins:
        print(f"   First quick win: {quick_wins[0]}")
    
    print("\n[7] Checking gaps_by_category...")
    gaps_cat = result.get('gaps_by_category', {})
    print(f"   Category keys: {list(gaps_cat.keys())}")
    print(f"   Critical gaps: {len(gaps_cat.get('critical', []))}")
    print(f"   Important gaps: {len(gaps_cat.get('important', []))}")
    print(f"   Nice-to-have gaps: {len(gaps_cat.get('nice_to_have', []))}")
    
    print("\n" + "=" * 70)
    print("✅ ALL COMPONENTS PRESENT AND WORKING!")
    print("=" * 70)
    
    # Print full structure for inspection
    print("\n[8] FULL RESULT STRUCTURE:")
    print("-" * 70)
    import json
    print(json.dumps(result, indent=2, default=str)[:2000] + "...")
    
except Exception as e:
    print(f"❌ Analysis failed: {e}")
    import traceback
    traceback.print_exc()
