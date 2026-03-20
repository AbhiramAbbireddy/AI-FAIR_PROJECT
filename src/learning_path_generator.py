"""
Learning Path Generator - Creates actionable month-by-month learning roadmap.

This module generates:
1. Linear learning timelines with milestones
2. Prerequisite handling
3. Quarterly grouping
4. Cross-job universal skills analysis
"""

import json
import os
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class LearningPathGenerator:
    """Generates actionable learning paths with timelines and milestones."""
    
    def __init__(self, learning_db_path: str = "data/learning_time_database.json"):
        """Initialize learning path generator.
        
        Args:
            learning_db_path: Path to learning time database
        """
        self.learning_db = self._load_json(learning_db_path)
        self.logger = logger
    
    def _load_json(self, filepath: str) -> dict:
        """Load JSON database."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"File {filepath} not found")
            return {}
    
    def check_prerequisites(self, skill: str, user_skills: List[str]) -> (bool, List[str]):
        """Check if user has prerequisites for learning this skill.
        
        Args:
            skill: Skill to check
            user_skills: User's current skills (both explicit + implicit)
            
        Returns:
            Tuple of (has_prerequisites, missing_prerequisites)
        """
        if skill.lower() not in self.learning_db:
            return True, []  # No prerequisites known
        
        prerequisites = self.learning_db[skill.lower()].get("prerequisites", [])
        user_skills_lower = set(s.lower() for s in user_skills)
        
        missing_prereqs = [
            prereq for prereq in prerequisites
            if prereq.lower() not in user_skills_lower
        ]
        
        has_prereqs = len(missing_prereqs) == 0
        return has_prereqs, missing_prereqs
    
    def generate_learning_timeline(self, ranked_skills: List[Dict],
                                  user_skills: List[str],
                                  current_match_score: float,
                                  max_skills: int = 10,
                                  max_months: int = 12) -> Dict:
        """Create month-by-month learning plan.
        
        Logic:
        1. Start with highest priority skill
        2. Check prerequisites - if missing, learn first
        3. Calculate cumulative time
        4. Show match score improvement at each step
        5. Group by quarters
        6. Stop if: timeline exceeds max_months OR score reaches 95%
        
        Args:
            ranked_skills: Ranked skill list from priority ranker
            user_skills: User's existing skills
            current_match_score: Current job match score
            max_skills: Maximum skills to include in timeline (default 10)
            max_months: Maximum timeline duration (default 12)
            
        Returns:
            Dict with timeline, milestones, and quarterly breakdown
        """
        timeline = []
        current_month = 0
        learned_skills = set(s.lower() for s in user_skills)
        current_score = current_match_score
        
        for skill_data in ranked_skills[:max_skills]:
            skill = skill_data["skill"]
            
            # Check prerequisites
            has_prereqs, missing_prereqs = self.check_prerequisites(skill, list(learned_skills))
            
            # Add prerequisite tasks if missing
            if not has_prereqs:
                for prereq_idx, prereq in enumerate(missing_prereqs):
                    prereq_time = self.learning_db.get(prereq.lower(), {}).get("months_to_learn", 1)
                    prereq_difficulty = self.learning_db.get(prereq.lower(), {}).get("difficulty", "easy")
                    
                    timeline.append({
                        "month": len([t for t in timeline if t["type"] == "prerequisite"]) + 1,
                        "week_range": f"{current_month*4+1}-{(current_month + prereq_time)*4}",
                        "skill": prereq,
                        "category": "CRITICAL",
                        "priority_score": 90,
                        "type": "prerequisite",
                        "start_month": current_month + 1,
                        "end_month": current_month + prereq_time,
                        "duration_months": prereq_time,
                        "difficulty": prereq_difficulty,
                        "match_score_after": round(current_score, 1),
                        "score_gain": 0,
                        "score_improvement": 0,
                        "estimated_hours_per_week": 6,
                        "is_prerequisite": True,
                        "reason": f"Prerequisite for {skill}",
                        
                        "learning_objectives": [
                            f"Understand {prereq} basics",
                            f"Apply {prereq} in practical scenarios"
                        ],
                        
                        "resources": [
                            {
                                "type": "course",
                                "name": f"{prereq} Fundamentals",
                                "platform": "YouTube/Udemy",
                                "duration": f"{prereq_time*4} hours",
                                "cost": "free/paid"
                            }
                        ],
                        
                        "practice_projects": [
                            f"Simple {prereq} exercise"
                        ],
                        
                        "success_criteria": [
                            f"Understand {prereq} concepts",
                            f"Ready to learn {skill}"
                        ]
                    })
                    
                    current_month += prereq_time
                    learned_skills.add(prereq.lower())
                    
                    # Break if timeline exceeds max
                    if current_month >= max_months:
                        break
            
            if current_month >= max_months or current_score >= 95:
                break
            
            # Add main skill
            skill_time = self.learning_db.get(skill.lower(), {}).get("months_to_learn", 3)
            
            # Estimate score improvement based on category
            score_improvement = self._estimate_score_improvement(skill_data.get("category", "IMPORTANT"))
            current_score = min(current_score + score_improvement, 100)
            
            difficulty = self.learning_db.get(skill.lower(), {}).get("difficulty", "moderate")
            resources = self.learning_db.get(skill.lower(), {}).get("resources", [])
            
            # Build detailed milestone (matching LLM structure)
            month_num = len([t for t in timeline if t["type"] == "priority"]) + 1
            
            timeline.append({
                "month": month_num,
                "week_range": f"{(current_month)*4+1}-{(current_month + skill_time)*4}",
                "skill": skill,
                "category": skill_data.get("category", "IMPORTANT"),
                "priority_score": skill_data.get("priority_score", 0),
                "type": "priority",
                "priority_rank": month_num,
                "start_month": current_month + 1,
                "end_month": current_month + skill_time,
                "duration_months": skill_time,
                "difficulty": difficulty,
                "match_score_after": round(current_score, 1),
                "score_gain": score_improvement,
                "score_improvement": round(score_improvement, 1),
                "estimated_hours_per_week": 8,
                "is_prerequisite": False,
                
                # Detailed learning information
                "learning_objectives": [
                    f"Master {skill} fundamentals",
                    f"Build practical projects using {skill}",
                    f"Understand real-world applications of {skill}"
                ],
                
                "resources": [
                    {
                        "type": "course",
                        "name": f"{skill} - Complete Guide",
                        "platform": "Udemy/Coursera",
                        "duration": f"{skill_time*4} hours",
                        "cost": "paid"
                    },
                    {
                        "type": "documentation",
                        "name": f"Official {skill} Documentation",
                        "platform": "Official",
                        "duration": "Self-paced",
                        "cost": "free"
                    },
                    {
                        "type": "tutorial",
                        "name": f"{skill} Tutorial Series",
                        "platform": "YouTube",
                        "duration": "8-10 hours",
                        "cost": "free"
                    }
                ] + [{"type": "resource", "name": r, "cost": "varies"} for r in resources[:2]],
                
                "practice_projects": [
                    f"Build a small project showcasing {skill}",
                    f"Create a portfolio piece using {skill}",
                    f"Solve coding challenges with {skill}"
                ],
                
                "success_criteria": [
                    f"Can explain {skill} concepts clearly",
                    f"Completed at least 2 projects",
                    f"Demonstrated proficiency in interviews"
                ],
                
                "learning_resources": resources[:3]
            })
            
            current_month += skill_time
            learned_skills.add(skill.lower())
            
            # Stop if timeline or score limit reached
            if current_month >= max_months or current_score >= 95:
                break
        
        return self._format_timeline(timeline, current_match_score, max_months)
    
    def _estimate_score_improvement(self, category: str) -> float:
        """Estimate how much learning this skill improves match score.
        
        Args:
            category: Skill category (CRITICAL/IMPORTANT/NICE_TO_HAVE)
            
        Returns:
            Estimated score improvement (0-10 points)
        """
        improvements = {
            "CRITICAL": 8.0,  # Critical skills give 8-point boost
            "IMPORTANT": 5.0,  # Important skills give 5-point boost
            "NICE_TO_HAVE": 2.0  # Nice-to-have gives 2-point boost
        }
        return improvements.get(category, 3.0)
    
    def _format_timeline(self, timeline: List[Dict], initial_score: float,
                        max_months: int) -> Dict:
        """Format timeline into readable structure.
        
        Args:
            timeline: List of timeline items
            initial_score: Starting match score
            max_months: Maximum timeline duration
            
        Returns:
            Formatted timeline dict
        """
        final_score = timeline[-1]["match_score_after"] if timeline else initial_score
        total_improvement = final_score - initial_score
        total_duration = timeline[-1]["end_month"] if timeline else 0
        
        # Wrap in "learning_path" key to match LLM generator format
        return {
            "learning_path": {
                "initial_match_score": round(initial_score, 1),
                "target_match_score": min(initial_score + (total_improvement or 20), 100),
                "final_match_score": round(final_score, 1),
                "total_improvement": round(total_improvement, 1),
                "improvement_percentage": round((total_improvement / initial_score * 100) if initial_score > 0 else 0, 1),
                "total_duration_months": total_duration,
                "estimated_hours_total": total_duration * 32,  # Estimate 32 hours per month
                "months_remaining": max_months - total_duration,
                "timeline_complete": total_duration <= max_months,
                "milestones": timeline,
                "quarters": self._group_by_quarter(timeline),
                "priority_skills": len([t for t in timeline if t["type"] == "priority"]),
                "prerequisite_skills": len([t for t in timeline if t["type"] == "prerequisite"]),
                "quick_wins": self._identify_quick_wins(timeline),
                "key_recommendations": [
                    "Start with highest priority skills",
                    "Build projects to reinforce learning",
                    "Join communities for peer support",
                    "Track progress and celebrate milestones"
                ]
            }
        }
    
    def _identify_quick_wins(self, timeline: List[Dict]) -> List[Dict]:
        """Identify high-impact, low-effort skills (quick wins).
        
        Quick wins are skills that:
        - Can be learned in 1-2 months
        - Improve match score significantly
        
        Args:
            timeline: List of timeline items
            
        Returns:
            List of quick win opportunities
        """
        quick_wins = []
        
        for skill_data in timeline[:3]:  # First few skills are typically quick wins
            if skill_data.get("duration_months", 3) <= 2:
                quick_wins.append({
                    "skill": skill_data.get("skill", "Unknown"),
                    "why_quick_win": "Can be learned quickly with high impact",
                    "time_needed": f"{skill_data.get('duration_months', 1)}-2 weeks",
                    "impact": f"+{skill_data.get('score_improvement', 5):.0f}% match score",
                    "difficulty": skill_data.get("difficulty", "moderate")
                })
        
        # If not enough quick wins, add the highest priority ones
        if len(quick_wins) < 3:
            for skill_data in timeline:
                if len(quick_wins) >= 3:
                    break
                if skill_data not in quick_wins:
                    score = skill_data.get("priority_score", 0)
                    if score > 70:  # High priority
                        quick_wins.append({
                            "skill": skill_data.get("skill", "Unknown"),
                            "why_quick_win": "High priority skill with good ROI",
                            "time_needed": f"{skill_data.get('duration_months', 1)}-{skill_data.get('duration_months', 1)+1} months",
                            "impact": f"+{skill_data.get('score_improvement', 5):.0f}% match score",
                            "difficulty": skill_data.get("difficulty", "moderate")
                        })
        
        return quick_wins
    
    def _group_by_quarter(self, timeline: List[Dict]) -> Dict[str, List[Dict]]:
        """Group skills by quarter for visualization.
        
        Args:
            timeline: List of timeline items
            
        Returns:
            Dict with Q1, Q2, Q3, Q4 keys
        """
        quarters = {"Q1": [], "Q2": [], "Q3": [], "Q4": []}
        
        for item in timeline:
            quarter_num = (item["end_month"] - 1) // 3  # 0-indexed quarter
            if quarter_num < 0:
                quarter_num = 0
            elif quarter_num > 3:
                quarter_num = 3
            
            quarter_key = f"Q{quarter_num + 1}"
            quarters[quarter_key].append(item)
        
        return quarters
    
    def generate_cross_job_analysis(self, ranked_skills_by_job: Dict[str, List[Dict]]) -> List[Dict]:
        """Find universal skills that help MULTIPLE top jobs.
        
        Logic:
        - Find skills appearing in 50%+ of jobs
        - Score by universality
        - These are "meta-skills" worth learning
        
        Input Example:
        {
            "Data Scientist": [ranked_skills],
            "ML Engineer": [ranked_skills]
        }
        
        Args:
            ranked_skills_by_job: Dict mapping job titles to ranked skill lists
            
        Returns:
            List of universal skills, sorted by universality score
        """
        skill_job_map = {}
        job_count = len(ranked_skills_by_job)
        
        for job_title, skills in ranked_skills_by_job.items():
            for skill_data in skills[:10]:  # Top 10 per job
                skill = skill_data["skill"].lower()
                
                if skill not in skill_job_map:
                    skill_job_map[skill] = {
                        "jobs": [],
                        "priority_scores": [],
                        "skill_original": skill_data["skill"]
                    }
                
                skill_job_map[skill]["jobs"].append(job_title)
                skill_job_map[skill]["priority_scores"].append(skill_data.get("priority_score", 0))
        
        # Find universal skills (appear in 50%+ of jobs)
        threshold = max(job_count // 2, 2)
        universal_skills = []
        
        for skill, data in skill_job_map.items():
            if len(data["jobs"]) >= threshold:
                universality_score = (len(data["jobs"]) / job_count) * 100
                avg_priority = sum(data["priority_scores"]) / len(data["priority_scores"])
                
                universal_skills.append({
                    "skill": data["skill_original"],
                    "appears_in_jobs": len(data["jobs"]),
                    "job_list": data["jobs"],
                    "universality_score": round(universality_score, 1),
                    "average_priority": round(avg_priority, 1),
                    "recommendation": self._generate_universal_skill_recommendation(universality_score, avg_priority)
                })
        
        # Sort by universality score
        universal_skills.sort(key=lambda x: x["universality_score"], reverse=True)
        
        return universal_skills
    
    def _generate_universal_skill_recommendation(self, universality: float,
                                               avg_priority: float) -> str:
        """Generate recommendation for universal skill.
        
        Args:
            universality: Universality score (0-100)
            avg_priority: Average priority across jobs
            
        Returns:
            Recommendation string
        """
        if universality > 80 and avg_priority > 80:
            return "MASTER SKILL: Learn this first! Will help you across multiple roles."
        elif universality > 60:
            return "Meta-skill: High ROI. Invest time here early."
        else:
            return "Useful across roles. Consider as secondary priority."
    
    def get_timeline_summary(self, timeline_data: Dict) -> str:
        """Generate readable timeline summary.
        
        Args:
            timeline_data: Output from generate_learning_timeline()
            
        Returns:
            Formatted summary string
        """
        summary = f"""
        Learning Path Summary
        ====================
        Current Match Score: {timeline_data['initial_match_score']}%
        Target Match Score: {timeline_data['final_match_score']}%
        Expected Improvement: +{timeline_data['total_improvement']}% ({timeline_data['improvement_percentage']}% increase)
        
        Timeline Duration: {timeline_data['total_duration_months']} months
        Skills to Learn: {timeline_data['priority_skills']} main + {timeline_data['prerequisite_skills']} prerequisites
        
        Quarterly Breakdown:
        """
        
        for quarter in ["Q1", "Q2", "Q3", "Q4"]:
            skills = timeline_data["quarters"][quarter]
            if skills:
                skill_names = [s["skill"] for s in skills]
                summary += f"\n        {quarter}: {', '.join(skill_names)}"
        
        return summary
