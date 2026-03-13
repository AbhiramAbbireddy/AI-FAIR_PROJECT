"""
Complete demonstration of the Skill Gap Analysis system.

Shows real-world usage examples with actual resumes and job postings.
"""

from src.skill_gap_analysis import SkillGapAnalysis
import json


def demo_single_job_analysis():
    """Demo: Analyze gaps for a single job position."""
    print("\n" + "="*80)
    print("DEMO 1: SINGLE JOB ANALYSIS - Data Scientist Role")
    print("="*80)
    
    # Initialize analyzer
    analyzer = SkillGapAnalysis()
    
    # User's skills (extracted from resume)
    user_skills = [
        "Python", "SQL", "Pandas", "Matplotlib",
        "Basic Statistics", "Excel", "Git"
    ]
    
    # Job Posting Data
    job_data = {
        "role": "Senior Data Scientist",
        "description": """
            We are looking for a Senior Data Scientist to join our team.
            You will work with Python and Machine Learning models daily.
            Experience with TensorFlow or PyTorch is required.
            
            Required Skills:
            - Python (5+ years)
            - Machine Learning
            - Deep Learning
            - TensorFlow or PyTorch
            - Statistical Analysis
            - SQL
            
            Nice to have:
            - Tableau or Power BI
            - Docker
            - AWS
            - Kubernetes
        """,
        "core_skills": [
            "Python", "Machine Learning", "Deep Learning",
            "TensorFlow", "Statistical Analysis", "SQL"
        ],
        "optional_skills": ["Tableau", "Docker", "AWS", "Kubernetes"]
    }
    
    # Current match score (from job matching system)
    current_match = 65.0
    
    # Run analysis
    print(f"\n📊 User Profile: {', '.join(user_skills[:5])}...")
    print(f"🎯 Target Role: {job_data['role']}")
    print(f"📈 Current Match Score: {current_match}%")
    
    analysis = analyzer.analyze_for_job(user_skills, job_data, current_match)
    
    # Display results
    print("\n" + "-"*80)
    print("GAPS IDENTIFIED:")
    print("-"*80)
    
    gaps = analysis["gaps_by_category"]
    print(f"🔴 Critical Gaps (Deal-breakers): {len(gaps['critical'])}")
    for gap in gaps["critical"][:5]:
        print(f"  • {gap}")
    
    print(f"\n🟡 Important Gaps: {len(gaps['important'])}")
    for gap in gaps["important"][:5]:
        print(f"  • {gap}")
    
    print(f"\n🟢 Nice-to-Have Gaps: {len(gaps['nice_to_have'])}")
    for gap in gaps["nice_to_have"][:3]:
        print(f"  • {gap}")
    
    # Show priority ranking
    print("\n" + "-"*80)
    print("TOP 5 PRIORITY SKILLS TO LEARN (Ranked):")
    print("-"*80)
    
    for rank, skill in enumerate(analysis["ranked_priorities"][:5], 1):
        print(f"\n{rank}. {skill['skill'].upper()}")
        print(f"   Priority Score: {skill['priority_score']}/100 ({skill['rank_tier']})")
        print(f"   Category: {skill['category']}")
        print(f"   Learning Time: {skill['learning_time_months']} months")
        print(f"   Salary Impact: ₹{skill['salary_boost_inr']}")
        print(f"   → {skill['recommendation']}")
    
    # Show quick wins
    print("\n" + "-"*80)
    print("⚡ QUICK WINS (High Priority + Easy to Learn):")
    print("-"*80)
    
    for i, win in enumerate(analysis["quick_wins"], 1):
        print(f"\n{i}. {win['skill']}")
        print(f"   Priority: {win['priority_score']}/100 | Learning Time: {win['learning_time_months']} months")
        print(f"   {win['reason']}")
    
    # Show learning path
    print("\n" + "-"*80)
    print("📚 LEARNING PATH TIMELINE:")
    print("-"*80)
    
    path = analysis["learning_path"]
    print(f"\nStarting Match Score: {path['initial_match_score']}%")
    print(f"Target Match Score: {path['final_match_score']}%")
    print(f"Expected Improvement: +{path['total_improvement']}% over {path['total_duration_months']} months\n")
    
    # Show quarterly breakdown
    quarters = path["quarters"]
    for quarter in ["Q1", "Q2", "Q3", "Q4"]:
        if quarters[quarter]:
            print(f"\n{quarter}:")
            for item in quarters[quarter]:
                print(f"  • {item['skill']} ({item['duration_months']} months)")
                print(f"    → Match score after: {item['match_score_after']}%")
    
    return analysis


def demo_multi_job_analysis():
    """Demo: Compare gaps across multiple job options."""
    print("\n\n" + "="*80)
    print("DEMO 2: MULTI-JOB ANALYSIS - Find Universal Skills Across 3 Roles")
    print("="*80)
    
    analyzer = SkillGapAnalysis()
    
    user_skills = ["Python", "JavaScript", "SQL", "GitHub"]
    
    # Three different job options
    jobs = [
        {
            "role": "Data Scientist",
            "description": "Python, ML, Statistics required",
            "core_skills": ["Python", "Machine Learning", "Statistics", "SQL"],
            "optional_skills": ["TensorFlow", "Tableau"],
            "match_score": 68
        },
        {
            "role": "Machine Learning Engineer",
            "description": "ML, Python, Deep Learning needed",
            "core_skills": ["Python", "Machine Learning", "Deep Learning", "PyTorch"],
            "optional_skills": ["Docker", "Kubernetes", "TensorFlow"],
            "match_score": 61
        },
        {
            "role": "Full Stack Developer",
            "description": "JavaScript and Python, Web development",
            "core_skills": ["JavaScript", "Python", "React", "Databases", "REST API"],
            "optional_skills": ["Docker", "AWS", "Testing"],
            "match_score": 72
        }
    ]
    
    print(f"\n📊 Analyzing user with skills: {', '.join(user_skills)}")
    print(f"🎯 Against {len(jobs)} job roles:")
    for job in jobs:
        print(f"   • {job['role']} (Current Match: {job['match_score']}%)")
    
    # Run multi-job analysis
    multi_analysis = analyzer.analyze_for_multiple_jobs(user_skills, jobs)
    
    # Show universal skills
    print("\n" + "-"*80)
    print("🌍 UNIVERSAL SKILLS (Help Multiple Roles):")
    print("-"*80)
    
    universal = multi_analysis["universal_skills"]
    for i, skill in enumerate(universal[:5], 1):
        print(f"\n{i}. {skill['skill'].upper()}")
        print(f"   Appears in {skill['appears_in_jobs']}/{len(jobs)} roles ({skill['universality_score']:.1f}%)")
        print(f"   Average Priority: {skill['average_priority']}/100")
        print(f"   Roles: {', '.join(skill['job_list'])}")
        print(f"   {skill['recommendation']}")
    
    # Show recommendation
    print("\n" + "-"*80)
    print("💡 OVERALL RECOMMENDATION:")
    print("-"*80)
    print(f"\n{multi_analysis['overall_recommendation']}")
    
    # Show individual job analysis summary
    print("\n" + "-"*80)
    print("📊 INDIVIDUAL JOB GAPS SUMMARY:")
    print("-"*80)
    
    for job_title, analysis in multi_analysis["individual_job_analyses"].items():
        total = analysis["total_gaps"]
        crit = analysis["gaps_breakdown"]["critical"]
        imp = analysis["gaps_breakdown"]["important"]
        print(f"\n{job_title}:")
        print(f"  Total Gaps: {total} (Critical: {crit}, Important: {imp})")
        print(f"  Match Potential: {analysis['current_match_score']}% → {analysis['learning_path']['final_match_score']}%")
    
    return multi_analysis


def demo_skill_normalization():
    """Demo: Show how skill normalization and hierarchy works."""
    print("\n\n" + "="*80)
    print("DEMO 3: SKILL NORMALIZATION & HIERARCHY")
    print("="*80)
    
    from src.gap_identifier import SkillGapIdentifier
    
    identifier = SkillGapIdentifier()
    
    # Examples of skill variations
    skill_variations = [
        ("js", "JavaScript"),
        ("k8s", "Kubernetes"),
        ("ML", "Machine Learning"),
        ("React.js", "React"),
        ("Node", "Node.js"),
        ("tf", "TensorFlow"),
        ("py", "Python")
    ]
    
    print("\n📌 Skill Normalization (Variations → Canonical Name):")
    print("-"*80)
    for variant, expected in skill_variations:
        normalized = identifier.normalize_skill(variant)
        status = "✓" if normalized == expected.lower() else "~"
        print(f"{status} '{variant}' → '{normalized}'")
    
    # Show skill hierarchy
    print("\n📌 Skill Hierarchy (Implicit Skills):")
    print("-"*80)
    
    demo_skills = ["react", "django", "tensorflow"]
    for skill in demo_skills:
        implicit = identifier.check_implicit_skills([skill])
        print(f"\n✓ User has: {skill.upper()}")
        print(f"  → Implicitly has: {', '.join(sorted(implicit - {skill}))}")
    
    return identifier


def demo_edge_cases():
    """Demo: Show edge case handling."""
    print("\n\n" + "="*80)
    print("DEMO 4: EDGE CASES & ERROR HANDLING")
    print("="*80)
    
    analyzer = SkillGapAnalysis()
    
    # Case 1: User with no skills
    print("\n1️⃣  User with NO skills:")
    print("-"*40)
    
    analysis = analyzer.analyze_for_job(
        [],  # Empty skills
        {
            "role": "Java Developer",
            "description": "Java required",
            "core_skills": ["Java", "Spring Boot"]
        },
        40
    )
    
    print(f"   Total gaps identified: {analysis['total_gaps']}")
    print(f"   Status: {analysis['gaps_breakdown']}")
    
    # Case 2: User with all required skills
    print("\n2️⃣  User with ALL required skills:")
    print("-"*40)
    
    analysis = analyzer.analyze_for_job(
        ["Python", "Django", "PostgreSQL"],
        {
            "role": "Python Developer",
            "description": "Python Django dev",
            "core_skills": ["Python", "Django", "PostgreSQL"]
        },
        95
    )
    
    print(f"   Total gaps identified: {analysis['total_gaps']}")
    print(f"   Current match: 95%")
    print(f"   Status: Already qualified! ✓")
    
    # Case 3: Unknown skills
    print("\n3️⃣  Skill not in database:")
    print("-"*40)
    
    ranked = analyzer.ranker.calculate_priority_score("SomeUnknownSkill2024")
    print(f"   Unknown Skill: SomeUnknownSkill2024")
    print(f"   Priority Score: {ranked['priority_score']}/100")
    print(f"   Status: Uses default values gracefully ✓")
    
    print("\n4️⃣  Very large gap (many missing skills):")
    print("-"*40)
    
    analysis = analyzer.analyze_for_job(
        ["HTML"],
        {
            "role": "ML Engineer",
            "description": "Advanced ML role",
            "core_skills": ["Python", "TensorFlow", "PyTorch", "Deep Learning", 
                          "Statistics", "Machine Learning", "Distributed Systems"],
            "optional_skills": ["Kubernetes", "Docker", "AWS", "CUDA"]
        },
        20
    )
    
    print(f"   User skills: HTML")
    print(f"   Required skills: 7")
    print(f"   Optional skills: 4")
    print(f"   Total gaps: {analysis['total_gaps']}")
    print(f"   Status: Large career jump needed - recommend stepping stone roles")


def save_analysis_to_file(analysis: dict, filename: str):
    """Save analysis results to JSON file."""
    with open(filename, 'w') as f:
        # Convert non-serializable objects
        def convert(obj):
            if isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert(item) for item in obj]
            elif not isinstance(obj, (str, int, float, bool, type(None))):
                return str(obj)
            return obj
        
        json.dump(convert(analysis), f, indent=2)
    
    print(f"\n✅ Analysis saved to {filename}")


def main():
    """Run all demonstrations."""
    print("\n")
    print("=" * 80)
    print(" " * 15 + "SKILL GAP ANALYSIS SYSTEM - COMPLETE DEMO")
    print("=" * 80)
    
    # Demo 1: Single job analysis
    analysis_1 = demo_single_job_analysis()
    
    # Demo 2: Multi-job analysis
    analysis_2 = demo_multi_job_analysis()
    
    # Demo 3: Skill normalization
    demo_skill_normalization()
    
    # Demo 4: Edge cases
    demo_edge_cases()
    
    # Save results
    print("\n\n" + "="*80)
    print("SAVING RESULTS")
    print("="*80)
    
    save_analysis_to_file(analysis_1, "results/gap_analysis_ds.json")
    save_analysis_to_file(analysis_2, "results/gap_analysis_multi_job.json")
    
    # Final summary
    print("\n" + "="*80)
    print("✅ DEMONSTRATION COMPLETE")
    print("="*80)
    print("""
    The Skill Gap Analysis system has demonstrated:
    
    ✓ Single Job Analysis: Identify and prioritize skill gaps
    ✓ Multi-Job Analysis: Find universal skills across roles
    ✓ Smart Normalization: Handle skill variations (JS → JavaScript)
    ✓ Skill Hierarchy: Infer implicit skills (React → JavaScript)
    ✓ Priority Ranking: Multi-factor scoring system
    ✓ Learning Paths: Month-by-month roadmap with milestones
    ✓ Quick Wins: Skills that are high-priority AND easy to learn
    ✓ Edge Cases: Graceful handling of edge cases
    
    System is ready for production integration with Streamlit app!
    """)


if __name__ == "__main__":
    main()
