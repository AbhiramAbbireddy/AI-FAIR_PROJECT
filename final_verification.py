#!/usr/bin/env python3
"""Final integration verification before deployment"""
import sys
sys.path.insert(0, '.')

print("=" * 70)
print("FINAL VERIFICATION - COMPREHENSIVE GAP ANALYSIS FIX")
print("=" * 70)

# Test 1: Syntax
print("\n[1/4] Checking streamlit_app.py syntax...")
try:
    import py_compile
    py_compile.compile('streamlit_app.py')
    print("    ✅ Syntax valid")
except Exception as e:
    print(f"    ❌ Syntax error: {e}")
    sys.exit(1)

# Test 2: Imports
print("\n[2/4] Testing all imports...")
try:
    from src.skill_gap_analysis import SkillGapAnalysis
    from src.gap_identifier import SkillGapIdentifier
    from src.gap_categorizer import GapCategorizer
    from src.priority_ranker import PriorityRanker
    from src.learning_path_generator import LearningPathGenerator
    print("    ✅ All modules import successfully")
except Exception as e:
    print(f"    ❌ Import error: {e}")
    sys.exit(1)

# Test 3: Analyzer instantiation
print("\n[3/4] Testing SkillGapAnalysis instantiation...")
try:
    analyzer = SkillGapAnalysis()
    print("    ✅ Analyzer created successfully")
except Exception as e:
    print(f"    ❌ Instantiation error: {e}")
    sys.exit(1)

# Test 4: Full analysis with output validation
print("\n[4/4] Testing full gap analysis pipeline...")
try:
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
    
    # Validate all components present
    assert 'ranked_priorities' in result, "Missing ranked_priorities"
    assert 'learning_path' in result, "Missing learning_path"
    assert 'quick_wins' in result, "Missing quick_wins"
    assert 'gaps_by_category' in result, "Missing gaps_by_category"
    
    # Validate structure - handle both LLM (nested) and rule-based (flat) structures
    learning_path = result['learning_path']
    milestones = []
    
    if isinstance(learning_path, dict):
        if 'learning_path' in learning_path:
            # LLM structure (nested)
            milestones = learning_path['learning_path'].get('milestones', [])
        else:
            # Rule-based structure (flat)
            milestones = learning_path.get('milestones', [])
    
    assert len(result['ranked_priorities']) > 0, "No ranked priorities"
    assert len(milestones) > 0, f"No milestones found. Structure keys: {list(learning_path.keys()) if isinstance(learning_path, dict) else 'Not a dict'}"
    assert 'critical' in result['gaps_by_category'], "Missing category"
    
    print("    ✅ Full analysis complete with all components")
    print(f"       - {len(result['ranked_priorities'])} priority skills ranked")
    print(f"       - {len(milestones)} milestones in path")
    print(f"       - {len(result['quick_wins'])} quick wins identified")
    print(f"       - Categories: {list(result['gaps_by_category'].keys())}")
    print(f"       - Powered by: {result.get('powered_by', 'Unknown')}")
    
except Exception as e:
    print(f"    ❌ Analysis error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ ALL VERIFICATION CHECKS PASSED")
print("=" * 70)
print("\n🚀 Ready to deploy!")
print("   Run: streamlit run streamlit_app.py")
print("\nExpected behavior:")
print("   1. Upload resume")
print("   2. Click 'Analyse Resume'")
print("   3. View enhanced 'Skill Gaps' tab with 4 views:")
print("      - Priority Ranking")
print("      - Learning Path")
print("      - Quick Wins")
print("      - Gap Breakdown")
print("=" * 70)
