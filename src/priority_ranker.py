"""
Skill Priority Ranker - Ranks missing skills using multi-factor scoring.

This module scores skills based on:
1. Job Importance (40%)
2. Market Demand (30%)
3. Learning Ease (20%)
4. Salary Impact (10%)
"""

import json
import os
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class PriorityRanker:
    """Ranks missing skills by learning priority using weighted factors."""
    
    def __init__(self, trend_data: Dict = None, learning_db_path: str = "data/learning_time_database.json",
                 salary_db_path: str = "data/salary_impact_database.json"):
        """Initialize ranker with trend and database data.
        
        Args:
            trend_data: Dict with trend information {skill: {growth_rate, trend}}
            learning_db_path: Path to learning time database
            salary_db_path: Path to salary impact database
        """
        self.trend_data = trend_data or {}
        self.learning_time_db = self._load_json(learning_db_path)
        self.salary_db = self._load_json(salary_db_path)
        
        # Weighted factors (must sum to 1.0)
        self.weights = {
            "job_importance": 0.40,
            "market_demand": 0.30,
            "learning_ease": 0.20,
            "salary_impact": 0.10
        }
        
        self.logger = logger
    
    def _load_json(self, filepath: str) -> dict:
        """Load JSON database file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"File {filepath} not found")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing {filepath}: {e}")
            return {}
    
    def calculate_job_importance(self, skill: str, job_description: str,
                                category: str, mention_count: int = 1) -> float:
        """Score job-specific importance (0-100).
        
        Logic:
        - CRITICAL category → 90-100
        - IMPORTANT category → 60-89
        - NICE_TO_HAVE → 30-59
        - Add bonus for mention count
        
        Args:
            skill: Skill to score
            job_description: Job description text
            category: Gap category (CRITICAL/IMPORTANT/NICE_TO_HAVE)
            mention_count: How many times skill mentioned in description
            
        Returns:
            Score 0-100
        """
        base_scores = {
            "CRITICAL": 95,
            "IMPORTANT": 75,
            "NICE_TO_HAVE": 40
        }
        
        base = base_scores.get(category, 50)
        
        # Bonus for multiple mentions (max 20 points)
        mention_bonus = min(mention_count * 5, 20)
        
        # Bonus if in job description (5 points)
        desc_bonus = 5 if job_description and skill.lower() in job_description.lower() else 0
        
        return min(base + mention_bonus + desc_bonus, 100)
    
    def calculate_market_demand(self, skill: str) -> float:
        """Score market demand based on trends (0-100).
        
        Growth rate interpretation:
        - >20% growth → 90-100 (very high demand)
        - 5-20% growth → 60-89 (high demand)
        - 0-5% growth → 40-59 (medium demand)
        - <0% growth → 10-39 (declining)
        
        Args:
            skill: Skill to evaluate
            
        Returns:
            Score 0-100
        """
        # Check trend data first
        if skill.lower() in self.trend_data:
            growth = self.trend_data[skill.lower()].get("growth_rate", 0)
            
            if growth > 20:
                return 95
            elif growth > 5:
                return 75
            elif growth > 0:
                return 50
            else:
                return 25
        
        # Check salary data for demand indicator
        if skill.lower() in self.salary_db:
            demand_map = {
                "very high": 95,
                "high": 75,
                "moderate": 55,
                "low": 25
            }
            demand = self.salary_db[skill.lower()].get("demand", "moderate")
            return demand_map.get(demand, 50)
        
        # Default if no data
        return 50
    
    def calculate_learning_ease(self, skill: str) -> float:
        """Score learning difficulty - inverse of time needed (0-100).
        
        Time to learn mapping:
        - 1-2 months → 90-100 (very easy)
        - 3-4 months → 70-89 (easy)
        - 5-6 months → 50-69 (moderate)
        - 7-12 months → 30-49 (hard)
        - 12+ months → 10-29 (very hard)
        
        Args:
            skill: Skill to evaluate
            
        Returns:
            Score 0-100
        """
        if skill.lower() not in self.learning_time_db:
            return 50  # Default if no data
        
        months = self.learning_time_db[skill.lower()].get("months_to_learn", 6)
        
        if months <= 2:
            return 95
        elif months <= 4:
            return 80
        elif months <= 6:
            return 60
        elif months <= 12:
            return 40
        else:
            return 20
    
    def calculate_salary_impact(self, skill: str) -> float:
        """Score salary potential (0-100).
        
        Salary boost mapping (INR):
        - >5L boost → 90-100
        - 2-5L boost → 60-89
        - <2L boost → 30-59
        
        Args:
            skill: Skill to evaluate
            
        Returns:
            Score 0-100
        """
        if skill.lower() not in self.salary_db:
            return 50  # Default
        
        salary_boost = self.salary_db[skill.lower()].get("average_boost_inr", 250000)
        
        if salary_boost > 500000:  # >5L
            return 95
        elif salary_boost > 200000:  # >2L
            return 75
        else:
            return 40
    
    def calculate_priority_score(self, skill: str, job_description: str = "",
                               category: str = "IMPORTANT",
                               mention_count: int = 1) -> Dict:
        """Calculate weighted priority score.
        
        Formula:
        Priority = (JobImportance × 0.4) + (MarketDemand × 0.3) +
                   (LearningEase × 0.2) + (SalaryImpact × 0.1)
        
        Args:
            skill: Skill to score
            job_description: Job description text
            category: Gap category
            mention_count: Mention frequency
            
        Returns:
            Dict with priority_score and breakdown
        """
        scores = {
            "job_importance": self.calculate_job_importance(skill, job_description, category, mention_count),
            "market_demand": self.calculate_market_demand(skill),
            "learning_ease": self.calculate_learning_ease(skill),
            "salary_impact": self.calculate_salary_impact(skill)
        }
        
        # Calculate weighted score
        priority_score = sum(
            scores[factor] * self.weights[factor]
            for factor in scores
        )
        
        # Get learning time for context
        learning_months = self.learning_time_db.get(skill.lower(), {}).get("months_to_learn", "Unknown")
        
        # Get salary impact for context
        salary_boost = self.salary_db.get(skill.lower(), {}).get("average_boost_inr", "N/A")
        
        return {
            "skill": skill,
            "priority_score": round(priority_score, 2),
            "rank_tier": self._rank_to_tier(priority_score),
            "breakdown": scores,
            "category": category,
            "learning_time_months": learning_months,
            "salary_boost_inr": salary_boost,
            "recommendation": self._generate_recommendation(priority_score, scores)
        }
    
    def _rank_to_tier(self, score: float) -> str:
        """Convert score to human-readable tier.
        
        Args:
            score: Priority score (0-100)
            
        Returns:
            Tier: "CRITICAL", "HIGH", "MEDIUM", or "LOW"
        """
        if score >= 85:
            return "CRITICAL"
        elif score >= 70:
            return "HIGH"
        elif score >= 50:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_recommendation(self, priority_score: float, scores: Dict) -> str:
        """Generate actionable recommendation based on scores.
        
        Args:
            priority_score: Overall priority score
            scores: Dictionary of factor scores
            
        Returns:
            Recommendation string
        """
        tier = self._rank_to_tier(priority_score)
        
        if tier == "CRITICAL":
            if scores["learning_ease"] > 80:
                return "URGENT: Quick win! Learn this skill immediately - high priority and relatively easy."
            else:
                return "URGENT: High priority despite learning difficulty. Start learning now."
        
        elif tier == "HIGH":
            if scores["salary_impact"] > 80:
                return "Prioritize this skill - significant salary boost potential."
            elif scores["market_demand"] > 80:
                return "Market-hot skill! Good career move to learn this soon."
            else:
                return "Important for this role. Learn within next 2-3 months."
        
        elif tier == "MEDIUM":
            if scores["learning_ease"] > 80:
                return "Good skill to have. Can be learned quickly if time permits."
            else:
                return "Useful but not urgent. Plan to learn within 6 months."
        
        else:
            return "Lower priority. Learn only if you have spare time."
    
    def rank_all_gaps(self, categorized_gaps: Dict[str, List[str]],
                     job_description: str = "") -> List[Dict]:
        """Rank all identified gaps.
        
        Args:
            categorized_gaps: Dict from gap_categorizer (critical/important/nice_to_have)
            job_description: Full job description text
            
        Returns:
            List of ranked skill dicts, sorted by priority score (descending)
        """
        all_ranked = []
        
        for category, skills in categorized_gaps.items():
            for skill in skills:
                ranked_skill = self.calculate_priority_score(
                    skill,
                    job_description,
                    category.upper()
                )
                all_ranked.append(ranked_skill)
        
        # Sort by priority score (descending)
        all_ranked.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return all_ranked
    
    def get_ranking_summary(self, ranked_skills: List[Dict]) -> str:
        """Generate readable ranking summary.
        
        Args:
            ranked_skills: List of ranked skill dicts
            
        Returns:
            Summary string
        """
        top_5 = ranked_skills[:5]
        
        summary = """
        Priority Ranking Summary (Top 5)
        ===============================
        """
        
        for i, skill_data in enumerate(top_5, 1):
            summary += f"""
        {i}. {skill_data['skill'].upper()} - Priority Score: {skill_data['priority_score']}/100
           Category: {skill_data['category']}
           Learning Time: {skill_data['learning_time_months']} months
           Salary Boost: ₹{skill_data['salary_boost_inr']} (approx)
           → {skill_data['recommendation']}
        """
        
        return summary
