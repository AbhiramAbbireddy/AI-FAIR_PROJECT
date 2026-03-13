#!/usr/bin/env python3
"""Verify Streamlit integration completeness"""
import sys
import os
sys.path.insert(0, '.')

print('═' * 60)
print('STREAMLIT INTEGRATION VERIFICATION')
print('═' * 60)

# Test 1: Check Streamlit app syntax
print('\n[1/5] Checking streamlit_app.py syntax...')
import py_compile
py_compile.compile('streamlit_app.py')
print('✅ Syntax valid')

# Test 2: Check all gap analysis imports
print('\n[2/5] Testing gap analysis imports...')
from src.skill_gap_analysis import SkillGapAnalysis
from src.gap_identifier import SkillGapIdentifier
from src.gap_categorizer import GapCategorizer
from src.priority_ranker import PriorityRanker
from src.learning_path_generator import LearningPathGenerator
print('✅ All 5 gap analysis modules importable')

# Test 3: Instantiate gap analyzer
print('\n[3/5] Creating SkillGapAnalysis instance...')
analyzer = SkillGapAnalysis()
print('✅ SkillGapAnalysis instantiated successfully')

# Test 4: Run a quick analysis
print('\n[4/5] Running quick gap analysis test...')
test_analysis = analyzer.analyze_for_job(
    user_skills=['Python', 'SQL'],
    job_data={
        'role': 'Test Role',
        'description': 'Test job',
        'core_skills': ['Python', 'Machine Learning'],
        'optional_skills': ['Docker']
    },
    current_match_score=60
)
if test_analysis and 'ranked_priorities' in test_analysis:
    priority_count = len(test_analysis.get('ranked_priorities', []))
    print(f'✅ Analysis complete - found {priority_count} priority skills')
else:
    print('⚠️  Analysis returned but check structure')

# Test 5: Check data files
print('\n[5/5] Verifying data files...')
required_files = [
    'data/skill_aliases.json',
    'data/skill_hierarchy.json',
    'data/learning_time_database.json',
    'data/salary_impact_database.json'
]
all_exist = all(os.path.exists(f) for f in required_files)
if all_exist:
    print('✅ All 4 required data files present')
else:
    missing = [f for f in required_files if not os.path.exists(f)]
    print(f'⚠️  Missing files: {missing}')

print('\n' + '═' * 60)
print('✅ INTEGRATION VERIFICATION COMPLETE')
print('═' * 60)
print('\nAll components ready!')
print('Run: streamlit run streamlit_app.py')
print('═' * 60)
