#!/usr/bin/env python3
"""Debug the learning path structure"""
import sys
sys.path.insert(0, '.')

from src.skill_gap_analysis import SkillGapAnalysis

analyzer = SkillGapAnalysis()

result = analyzer.analyze_for_job(
    user_skills=['Python', 'SQL'],
    job_data={
        'role': 'Data Scientist',
        'description': 'Looking for Python, ML, TensorFlow',
        'core_skills': ['Python', 'Machine Learning', 'TensorFlow'],
        'optional_skills': ['Docker']
    },
    current_match_score=60
)

print("Result keys:", list(result.keys()))
print("\nLearning path type:", type(result['learning_path']))
print("Learning path keys:", list(result['learning_path'].keys()) if isinstance(result['learning_path'], dict) else "Not a dict")

if isinstance(result['learning_path'], dict):
    if 'milestones' in result['learning_path']:
        print(f"\n✓ Has 'milestones' key directly: {len(result['learning_path']['milestones'])} items")
    elif 'learning_path' in result['learning_path']:
        inner = result['learning_path']['learning_path']
        print(f"\n✓ Has nested 'learning_path': {list(inner.keys()) if isinstance(inner, dict) else 'Not a dict'}")
        if isinstance(inner, dict) and 'milestones' in inner:
            print(f"  - Nested milestones: {len(inner['milestones'])} items")
    else:
        print("\n✗ No 'milestones' key found")
        print(f"  Available keys: {list(result['learning_path'].keys())}")

print("\nPowered by:", result.get('powered_by'))
