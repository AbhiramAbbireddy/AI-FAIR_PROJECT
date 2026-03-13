"""
Skill Gap Categorizer - Categorizes missing skills into Critical/Important/Nice-to-have.

This module analyzes job descriptions and skill importance to categorize gaps.
"""

import re
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class GapCategorizer:
    """Categorizes identified skill gaps by importance level."""
    
    def __init__(self):
        """Initialize categorizer with keyword patterns."""
        # Keywords that indicate critical importance
        self.critical_keywords = [
            "required", "must have", "mandatory", "essential",
            "critical", "core", "prerequisite", "need"
        ]
        
        # Keywords that indicate optional importance
        self.optional_keywords = [
            "nice to have", "preferred", "beneficial", "bonus",
            "plus", "helpful", "optional", "advantage"
        ]
        
        # Keywords that indicate high frequency/importance
        self.important_keywords = [
            "experience with", "familiar with", "knowledge of",
            "working knowledge", "proficiency", "expertise",
            "demonstrated experience"
        ]
        
        self.logger = logger
    
    def _count_mentions(self, skill: str, text: str) -> int:
        """Count how many times a skill is mentioned in text.
        
        Uses case-insensitive regex matching.
        
        Args:
            skill: Skill to count
            text: Text to search
            
        Returns:
            Number of mentions
        """
        if not text or not skill:
            return 0
        
        # Create regex pattern for skill with word boundaries
        pattern = r'\b' + re.escape(skill) + r'\b'
        matches = re.findall(pattern, text, re.IGNORECASE)
        return len(matches)
    
    def _get_skill_context(self, skill: str, text: str, context_chars: int = 150) -> str:
        """Extract surrounding text where skill is mentioned.
        
        Gets a window of text around the skill mention.
        
        Args:
            skill: Skill to find
            text: Text to search
            context_chars: Characters to include before/after skill
            
        Returns:
            Context string containing the skill
        """
        if not text or not skill:
            return ""
        
        pattern = r'.{0,' + str(context_chars) + r'}\b' + re.escape(skill) + r'\b.{0,' + str(context_chars) + r'}'
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        
        return " ".join(matches) if matches else ""
    
    def _is_near_keyword(self, skill: str, text: str, keywords: List[str],
                        distance: int = 100) -> bool:
        """Check if skill is mentioned near any keyword.
        
        Args:
            skill: Skill to check
            text: Text to search
            keywords: Keywords to search for
            distance: Character distance threshold
            
        Returns:
            True if skill is near any keyword
        """
        if not text or not skill:
            return False
        
        skill_pos = text.lower().find(skill.lower())
        if skill_pos == -1:
            return False
        
        for keyword in keywords:
            keyword_pos = text.lower().find(keyword.lower())
            if keyword_pos != -1:
                if abs(skill_pos - keyword_pos) <= distance:
                    return True
        
        return False
    
    def categorize_gap(self, skill: str, job_description: str,
                      job_required_skills: List[str]) -> str:
        """Determine if a gap is Critical, Important, or Nice-to-have.
        
        Logic:
        1. If in job_required_skills → CRITICAL
        2. If mentioned 3+ times → IMPORTANT
        3. If near "required" keyword → CRITICAL
        4. If near "optional" keyword → NICE_TO_HAVE
        5. Otherwise → IMPORTANT
        
        Args:
            skill: Skill to categorize
            job_description: Full job description text
            job_required_skills: List of explicitly required skills
            
        Returns:
            Category: "CRITICAL", "IMPORTANT", or "NICE_TO_HAVE"
        """
        # Check if explicitly required
        if any(skill.lower() == req.lower() for req in job_required_skills):
            return "CRITICAL"
        
        mention_count = self._count_mentions(skill, job_description)
        
        # High frequency mentions = important
        if mention_count >= 3:
            return "IMPORTANT"
        
        # Check keyword context
        if self._is_near_keyword(skill, job_description, self.critical_keywords):
            return "CRITICAL"
        
        if self._is_near_keyword(skill, job_description, self.optional_keywords):
            return "NICE_TO_HAVE"
        
        # Check if mentioned in important context
        if mention_count >= 2:
            return "IMPORTANT"
        
        # Default
        return "IMPORTANT"
    
    def categorize_all_gaps(self, gaps: List[str], job_description: str,
                          job_required_skills: List[str]) -> Dict[str, List[str]]:
        """Categorize all identified gaps.
        
        Args:
            gaps: List of missing skills
            job_description: Full job description text
            job_required_skills: List of explicitly required skills
            
        Returns:
            Dict with keys "critical", "important", "nice_to_have"
        """
        categorized = {
            "critical": [],
            "important": [],
            "nice_to_have": []
        }
        
        for gap in gaps:
            category = self.categorize_gap(gap, job_description, job_required_skills)
            categorized[category.lower()].append(gap)
        
        return categorized
    
    def get_categorization_confidence(self, skill: str, job_description: str,
                                     job_required_skills: List[str]) -> float:
        """Get confidence score (0-1) for the categorization.
        
        Higher confidence indicates more certain categorization.
        
        Args:
            skill: Skill to evaluate
            job_description: Job description text
            job_required_skills: List of required skills
            
        Returns:
            Confidence score 0-1
        """
        confidence = 0.5  # Start at neutral
        
        # High confidence if explicitly required
        if any(skill.lower() == req.lower() for req in job_required_skills):
            return 0.95
        
        mention_count = self._count_mentions(skill, job_description)
        
        # Increase confidence with mention count
        if mention_count >= 3:
            confidence += 0.3
        elif mention_count == 2:
            confidence += 0.2
        elif mention_count == 1:
            confidence += 0.1
        
        # Increase confidence if near critical keywords
        if self._is_near_keyword(skill, job_description, self.critical_keywords):
            confidence = min(confidence + 0.35, 0.95)
        
        # Decrease confidence if near optional keywords
        if self._is_near_keyword(skill, job_description, self.optional_keywords):
            confidence = max(confidence - 0.2, 0.1)
        
        return min(confidence, 0.95)
    
    def get_categorization_summary(self, categorized: Dict[str, List[str]]) -> str:
        """Generate readable categorization summary.
        
        Args:
            categorized: Dict from categorize_all_gaps()
            
        Returns:
            Summary string
        """
        summary = f"""
        Gap Categorization Summary
        =========================
        Critical (Deal-breakers): {len(categorized['critical'])} skills
        - {', '.join(categorized['critical']) if categorized['critical'] else 'None'}
        
        Important (Strongly Preferred): {len(categorized['important'])} skills
        - {', '.join(categorized['important']) if categorized['important'] else 'None'}
        
        Nice-to-Have (Bonus Points): {len(categorized['nice_to_have'])} skills
        - {', '.join(categorized['nice_to_have']) if categorized['nice_to_have'] else 'None'}
        """
        return summary
