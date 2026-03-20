"""
Skill Gap Analysis Orchestrator - Ties all components together.

This is the main API for performing complete skill gap analysis.
"""

from src.gap_identifier import SkillGapIdentifier
from src.gap_categorizer import GapCategorizer
from src.priority_ranker import PriorityRanker
from src.learning_path_generator import LearningPathGenerator
from typing import Dict, List, Optional
import logging

# Try to import LLM generator, but don't fail if it's not available
try:
    from src.llm_learning_path_generator import LLMLearningPathGenerator
    HAS_LLM = True
except ImportError as e:
    HAS_LLM = False
    LLMLearningPathGenerator = None

logger = logging.getLogger(__name__)


class SkillGapAnalysis:
    """Complete skill gap analysis system - orchestrates all components."""
    
    def __init__(self, trend_data: Dict = None, data_dir: str = "data"):
        """Initialize the skill gap analysis system.
        
        Args:
            trend_data: Optional trend data {skill: {growth_rate, trend}}
            data_dir: Directory containing data files
        """
        self.identifier = SkillGapIdentifier(data_dir=data_dir)
        self.categorizer = GapCategorizer()
        self.ranker = PriorityRanker(trend_data=trend_data)
        self.path_generator = LearningPathGenerator()
        self.logger = logger
        
        # Initialize LLM-powered learning path generator (optional)
        self.llm_generator = None
        self.use_llm = False
        
        # Only try to load LLM if the module was successfully imported
        if HAS_LLM and LLMLearningPathGenerator:
            try:
                self.llm_generator = LLMLearningPathGenerator()
                self.use_llm = True
                print("✓ LLM-powered learning paths enabled (Gemini API)")
            except Exception as e:
                print(f"⚠ LLM not available: {e}")
                print("  Using rule-based learning paths instead")
        else:
            print("⚠ LLM module not available")
            print("  Using rule-based learning paths instead")
    
    def analyze_for_job(self, user_skills: List[str], job_data: Dict,
                       current_match_score: float = 0, user_context: Optional[Dict] = None,
                       trend_data: Optional[Dict] = None) -> Dict:
        """Complete skill gap analysis for ONE job.
        
        Full pipeline:
        1. Identify gaps
        2. Categorize gaps
        3. Rank by priority
        4. Generate learning path (LLM or rule-based)
        
        Args:
            user_skills: List of user's skills
            job_data: Job information dict with keys:
                - role: Job title
                - description: Job description text
                - core_skills: List of required skills
                - optional_skills: List of optional skills (optional)
            current_match_score: Current job match score (0-100)
            user_context: Optional dict with user preferences:
                - experience_level: "beginner", "intermediate", "advanced"
                - available_time: "part-time", "full-time", "minimal"
                - learning_style: "hands-on", "theory-first", "mixed"
                - budget: "free", "budget-friendly", "willing-to-invest"
            
        Returns:
            Comprehensive analysis dict with:
            - gap identification
            - categorization
            - priority ranking
            - learning timeline
            - quick wins
            - long-term investments
        """
        if trend_data:
            self.ranker.update_trend_data(trend_data)

        # Provide default current_match_score if not provided
        if current_match_score <= 0:
            current_match_score = 50  # Default placeholder
        
        # Step 1: Identify gaps
        gaps = self.identifier.identify_gaps(
            user_skills,
            job_data.get("core_skills", []),
            job_data.get("optional_skills", [])
        )
        
        # Collect all gaps for categorization
        all_gaps = (
            gaps["critical_gaps"] +
            gaps["important_gaps"] +
            gaps["nice_to_have_gaps"]
        )
        
        # Step 2: Categorize gaps
        categorized = self.categorizer.categorize_all_gaps(
            all_gaps,
            job_data.get("description", ""),
            job_data.get("core_skills", [])
        )
        
        # Step 3: Rank by priority
        ranked = self.ranker.rank_all_gaps(
            categorized,
            job_data.get("description", "")
        )
        
        # Step 4: Generate learning path
        existing_skills = gaps["user_skills_with_implicit"]
        
        # Try LLM-powered learning path first, fallback to rule-based
        if self.use_llm and self.llm_generator:
            try:
                learning_path = self.llm_generator.generate_learning_path(
                    user_skills,
                    ranked,
                    job_data.get("role", "Unknown"),
                    job_data.get("description", ""),
                    current_match_score,
                    user_context
                )
            except Exception as e:
                print(f"⚠ LLM path generation failed: {e}")
                print("  Falling back to rule-based path...")
                learning_path = self.path_generator.generate_learning_timeline(
                    ranked,
                    existing_skills,
                    current_match_score
                )
        else:
            # Use rule-based learning path
            learning_path = self.path_generator.generate_learning_timeline(
                ranked,
                existing_skills,
                current_match_score
            )
        
        # Analysis complete
        return {
            "job_title": job_data.get("role", "Unknown"),
            "current_match_score": current_match_score,
            "total_gaps": gaps["total_gap_count"],
            "gaps_breakdown": {
                "critical": len(gaps["critical_gaps"]),
                "important": len(gaps["important_gaps"]),
                "nice_to_have": len(gaps["nice_to_have_gaps"])
            },
            "gaps_by_category": categorized,
            "ranked_priorities": ranked,
            "learning_path": learning_path,
            "quick_wins": self._identify_quick_wins(ranked),
            "long_term_investments": self._identify_long_term(ranked),
            "user_analysis": {
                "explicit_skills": len(gaps["user_skills_explicit"]),
                "implicit_skills": len(gaps["implicit_skills"]),
                "total_effective_skills": len(gaps["user_skills_with_implicit"])
            },
            "powered_by": "Gemini AI (LLM)" if self.use_llm else "Rule-based"
        }
    
    def analyze_for_multiple_jobs(self, user_skills: List[str],
                                 top_jobs_data: List[Dict]) -> Dict:
        """Analyze gaps for TOP N matching jobs.
        
        Also performs cross-job analysis to find universal skills.
        
        Args:
            user_skills: User's skills
            top_jobs_data: List of top job options with match scores
            
        Returns:
            Dict with individual analyses + cross-job insights
        """
        all_analyses = {}
        ranked_skills_by_job = {}
        
        # Analyze each job individually
        for job_data in top_jobs_data:
            job_title = job_data.get("role", "Unknown")
            match_score = job_data.get("match_score", 50)
            
            analysis = self.analyze_for_job(
                user_skills,
                job_data,
                match_score
            )
            
            all_analyses[job_title] = analysis
            ranked_skills_by_job[job_title] = analysis["ranked_priorities"]
        
        # Cross-job analysis
        universal_skills = self.path_generator.generate_cross_job_analysis(
            ranked_skills_by_job
        )
        
        return {
            "individual_job_analyses": all_analyses,
            "universal_skills": universal_skills,
            "overall_recommendation": self._generate_overall_recommendation(universal_skills, all_analyses),
            "total_jobs_analyzed": len(top_jobs_data),
            "summary": self._generate_multi_job_summary(all_analyses, universal_skills)
        }
    
    def _identify_quick_wins(self, ranked_skills: List[Dict]) -> List[Dict]:
        """Identify quick-win skills (high priority + easy to learn).
        
        Args:
            ranked_skills: Ranked skill list
            
        Returns:
            Top 3 quick-win skills
        """
        quick_wins = []
        
        for skill in ranked_skills:
            learning_ease = skill["breakdown"].get("learning_ease", 50)
            priority = skill["priority_score"]
            
            # Quick wins: high priority + easy (>80 ease + >70 priority)
            if learning_ease > 80 and priority > 70:
                quick_wins.append({
                    "skill": skill["skill"],
                    "priority_score": priority,
                    "learning_ease": learning_ease,
                    "learning_time_months": skill.get("learning_time_months", "Unknown"),
                    "reason": f"High priority ({priority:.0f}/100) and quick to learn ({skill.get('learning_time_months')} months)"
                })
        
        # Return top 3
        return quick_wins[:3]
    
    def _identify_long_term(self, ranked_skills: List[Dict]) -> List[Dict]:
        """Identify long-term investments (high priority + hard to learn).
        
        Args:
            ranked_skills: Ranked skill list
            
        Returns:
            Top 3 long-term investment skills
        """
        long_term = []
        
        for skill in ranked_skills:
            learning_ease = skill["breakdown"].get("learning_ease", 50)
            priority = skill["priority_score"]
            
            # Long term: high priority + hard (<50 ease + >75 priority)
            if learning_ease < 50 and priority > 75:
                long_term.append({
                    "skill": skill["skill"],
                    "priority_score": priority,
                    "learning_ease": learning_ease,
                    "learning_time_months": skill.get("learning_time_months", "Unknown"),
                    "reason": f"High priority ({priority:.0f}/100) but requires time ({skill.get('learning_time_months')} months)"
                })
        
        # Return top 3
        return long_term[:3]
    
    def _generate_overall_recommendation(self, universal_skills: List[Dict],
                                       all_analyses: Dict[str, Dict]) -> str:
        """Generate final recommendation for user.
        
        Args:
            universal_skills: Cross-job universal skills
            all_analyses: Individual job analyses
            
        Returns:
            Recommendation string
        """
        if not universal_skills:
            return "Focus on specific job requirements individually. Each role has unique needs."
        
        top_universal = universal_skills[0]
        num_jobs = len(all_analyses)
        
        return (
            f"🎯 PRIMARY RECOMMENDATION:\n"
            f"Learning '{top_universal['skill']}' should be your #1 priority.\n"
            f"This skill will improve your match for {top_universal['appears_in_jobs']} out of {num_jobs} roles "
            f"({top_universal['universality_score']:.1f}% universality).\n"
            f"Priority Score: {top_universal['average_priority']:.1f}/100\n"
            f"{top_universal['recommendation']}"
        )
    
    def _generate_multi_job_summary(self, all_analyses: Dict, universal_skills: List[Dict]) -> str:
        """Generate summary of multi-job analysis.
        
        Args:
            all_analyses: Individual analyses
            universal_skills: Universal skills across jobs
            
        Returns:
            Summary string
        """
        total_jobs = len(all_analyses)
        avg_score = sum(a["current_match_score"] for a in all_analyses.values()) / total_jobs if all_analyses else 0
        total_unique_gaps = len(set(
            s for analysis in all_analyses.values()
            for gap_list in analysis["gaps_by_category"].values()
            for s in gap_list
        ))
        
        summary = (
            f"Analyzed {total_jobs} jobs\n"
            f"Average match score: {avg_score:.1f}%\n"
            f"Total unique skill gaps: {total_unique_gaps}\n"
            f"Universal skills (appear in 50%+ of roles): {len(universal_skills)}"
        )
        
        return summary
    
    def get_full_report(self, analysis: Dict) -> str:
        """Generate comprehensive text report from analysis.
        
        Args:
            analysis: Result from analyze_for_job() or analyze_for_multiple_jobs()
            
        Returns:
            Formatted report string
        """
        report = f"""
        ╔══════════════════════════════════════════════════════════════╗
        ║          SKILL GAP ANALYSIS REPORT                           ║
        ╚══════════════════════════════════════════════════════════════╝
        
        Job Title: {analysis.get('job_title', 'Multiple Jobs')}
        Current Match Score: {analysis.get('current_match_score', 'N/A')}%
        
        ┌─ SKILLS SUMMARY ─────────────────────────────────────────────┐
        Total Skills Missing: {analysis.get('total_gaps', 'N/A')}
        
        Gap Breakdown:
        - Critical: {analysis.get('gaps_breakdown', {}).get('critical', 0)}
        - Important: {analysis.get('gaps_breakdown', {}).get('important', 0)}
        - Nice-to-Have: {analysis.get('gaps_breakdown', {}).get('nice_to_have', 0)}
        
        Your Skills:
        - Explicit: {analysis.get('user_analysis', {}).get('explicit_skills', 0)}
        - Implicit (inherited): {analysis.get('user_analysis', {}).get('implicit_skills', 0)}
        - Total Effective: {analysis.get('user_analysis', {}).get('total_effective_skills', 0)}
        └──────────────────────────────────────────────────────────────┘
        
        ┌─ TOP QUICK WINS ─────────────────────────────────────────────┐
        (High priority + Easy to learn - Start Here!)
        """
        
        for i, win in enumerate(analysis.get("quick_wins", []), 1):
            report += f"\n        {i}. {win['skill']} ({win['learning_time_months']} months)"
            report += f"\n           → {win['reason']}"
        
        report += f"""
        └──────────────────────────────────────────────────────────────┘
        
        ┌─ TOP 5 PRIORITY SKILLS ──────────────────────────────────────┐
        """
        
        for i, skill in enumerate(analysis.get("ranked_priorities", [])[:5], 1):
            report += f"\n        {i}. {skill['skill']} - Priority: {skill['priority_score']}/100"
            report += f"\n           Category: {skill['category']}"
            report += f"\n           Learning Time: {skill.get('learning_time_months', 'N/A')} months"
            report += f"\n           Salary Impact: ₹{skill.get('salary_boost_inr', 'N/A')}"
        
        report += f"""
        └──────────────────────────────────────────────────────────────┘
        """
        
        return report
