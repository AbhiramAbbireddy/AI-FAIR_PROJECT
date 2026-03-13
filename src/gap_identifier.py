"""
Skill Gap Identifier - Identifies missing skills by comparing user skills with job requirements.

This module handles:
1. Skill normalization (JS -> JavaScript)
2. Fuzzy matching for typos/variations
3. Skill hierarchy (React implies JavaScript)
4. Gap type classification (hard vs soft vs related gaps)
"""

import json
import os
from typing import Dict, List, Set, Tuple
from fuzzywuzzy import fuzz
import logging

logger = logging.getLogger(__name__)


class SkillGapIdentifier:
    """Identifies skill gaps between user profile and job requirements."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the gap identifier with skill aliases and hierarchy.
        
        Args:
            data_dir: Directory containing skill_aliases.json and skill_hierarchy.json
        """
        self.data_dir = data_dir
        self.skill_aliases = self._load_json("skill_aliases.json")
        self.skill_hierarchy = self._load_json("skill_hierarchy.json")
        self.fuzzy_threshold = 85  # Match quality threshold
        self.logger = logger
    
    def _load_json(self, filename: str) -> dict:
        """Load JSON data file from data directory."""
        filepath = os.path.join(self.data_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"File {filepath} not found. Using empty dict.")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing {filepath}: {e}")
            return {}
    
    def normalize_skill(self, skill: str) -> str:
        """Convert skill to canonical form using aliases.
        
        Process:
        1. Convert to lowercase
        2. Strip whitespace
        3. Check aliases mapping
        4. Return canonical name
        
        Args:
            skill: Raw skill string
            
        Returns:
            Normalized skill name
        """
        if not skill:
            return ""
        
        # Clean input
        skill_clean = skill.strip().lower()
        
        # Direct alias match
        if skill_clean in self.skill_aliases:
            return self.skill_aliases[skill_clean].lower()
        
        # Return as-is if no alias found
        return skill_clean
    
    def check_implicit_skills(self, user_skills: List[str]) -> Set[str]:
        """Infer skills based on skill hierarchy.
        
        Example: If user has "React", they implicitly have "JavaScript"
        
        Args:
            user_skills: List of user's skills
            
        Returns:
            Set of explicit + implicit skills
        """
        normalized_user_skills = set(self.normalize_skill(s) for s in user_skills)
        implicit_skills = set(normalized_user_skills)
        
        # Add implied skills
        for skill in normalized_user_skills:
            if skill in self.skill_hierarchy:
                implies = self.skill_hierarchy[skill].get("implies", [])
                for implied_skill in implies:
                    implied_norm = self.normalize_skill(implied_skill)
                    implicit_skills.add(implied_norm)
        
        return implicit_skills
    
    def fuzzy_match_skill(self, skill: str, skill_list: List[str], 
                         threshold: int = None) -> Tuple[str, int]:
        """Match skill to most similar skill in list (handles typos/variations).
        
        Uses fuzzy string matching to find the best match even with typos.
        
        Args:
            skill: Skill to match
            skill_list: List of candidate skills to match against
            threshold: Match quality threshold (0-100), default 85
            
        Returns:
            Tuple of (best_match_skill, match_score)
        """
        if threshold is None:
            threshold = self.fuzzy_threshold
        
        if not skill_list:
            return None, 0
        
        skill_norm = self.normalize_skill(skill)
        best_match = None
        best_score = 0
        
        for candidate in skill_list:
            candidate_norm = self.normalize_skill(candidate)
            score = fuzz.token_set_ratio(skill_norm, candidate_norm)
            
            if score > best_score:
                best_score = score
                best_match = candidate_norm
        
        if best_score >= threshold:
            return best_match, best_score
        
        return None, 0
    
    def identify_gaps(self, user_skills: List[str], job_required: List[str],
                     job_optional: List[str] = None) -> Dict:
        """Main gap identification logic.
        
        Identifies three types of gaps:
        1. Hard gaps: Required skills missing
        2. Important gaps: Often mentioned but missing
        3. Soft gaps: Optional skills missing
        
        Args:
            user_skills: Skills the user has
            job_required: Skills required by the job
            job_optional: Optional skills for the job (default: empty list)
            
        Returns:
            Dict with critical_gaps, important_gaps, nice_to_have_gaps, etc.
        """
        if job_optional is None:
            job_optional = []
        
        # Normalize user skills + infer implicit skills
        user_skills_explicit = set(self.normalize_skill(s) for s in user_skills)
        user_skills_all = self.check_implicit_skills(user_skills)
        
        # Normalize job skills
        job_required_norm = [self.normalize_skill(s) for s in job_required]
        job_optional_norm = [self.normalize_skill(s) for s in job_optional]
        
        # Identify hard gaps (required but missing)
        critical_gaps = []
        for req_skill in job_required_norm:
            if req_skill not in user_skills_all:
                # Try fuzzy match
                match, score = self.fuzzy_match_skill(req_skill, list(user_skills_all))
                if not match:  # Only gap if no fuzzy match found
                    critical_gaps.append(req_skill)
        
        # Identify soft gaps (optional but missing)
        nice_to_have_gaps = []
        for opt_skill in job_optional_norm:
            if opt_skill not in user_skills_all:
                match, score = self.fuzzy_match_skill(opt_skill, list(user_skills_all))
                if not match:
                    nice_to_have_gaps.append(opt_skill)
        
        # Important gaps are everything not in critical or nice_to_have
        # (Usually middle-tier required skills)
        important_gaps = [
            s for s in job_required_norm 
            if s not in critical_gaps and s not in user_skills_all
        ]
        
        return {
            "critical_gaps": critical_gaps,
            "important_gaps": important_gaps,
            "nice_to_have_gaps": nice_to_have_gaps,
            "total_gap_count": len(critical_gaps) + len(important_gaps) + len(nice_to_have_gaps),
            "user_skills_explicit": list(user_skills_explicit),
            "user_skills_with_implicit": list(user_skills_all),
            "implicit_skills": list(user_skills_all - user_skills_explicit)
        }
    
    def identify_related_gaps(self, user_skills: List[str], job_domain: str) -> List[str]:
        """Identify skills related to job domain but not explicitly required.
        
        Example: For a Data Science role, identify if user lacks statistics/math
        
        Args:
            user_skills: User's skills
            job_domain: Job domain/category (e.g., "data science", "frontend")
            
        Returns:
            List of related skills that would help in the domain
        """
        domain_skills_map = {
            "frontend": ["html", "css", "responsive design", "web accessibility"],
            "backend": ["databases", "api design", "caching", "security"],
            "data engineer": ["etl", "databases", "distributed systems", "monitoring"],
            "data scientist": ["statistics", "mathematics", "domain knowledge"],
            "machine learning": ["deep learning", "mathematics", "statistics", "feature engineering"],
            "devops": ["linux", "networking", "monitoring", "disaster recovery"],
            "security": ["penetration testing", "cryptography", "incident response"],
            "qa": ["test automation", "performance testing", "bug tracking"]
        }
        
        user_skills_norm = self.check_implicit_skills(user_skills)
        domain_key = job_domain.lower()
        
        related_gaps = []
        for domain_key_candidate in domain_skills_map:
            if domain_key_candidate in domain_key or domain_key in domain_key_candidate:
                for skill in domain_skills_map[domain_key_candidate]:
                    if self.normalize_skill(skill) not in user_skills_norm:
                        related_gaps.append(skill)
        
        return list(set(related_gaps))  # Remove duplicates
    
    def get_gap_summary(self, gaps: Dict) -> str:
        """Generate human-readable gap summary.
        
        Args:
            gaps: Gap identification result dict
            
        Returns:
            Summary string
        """
        summary = f"""
        Gap Analysis Summary
        ====================
        Total Skills Missing: {gaps['total_gap_count']}
        
        Critical Gaps (Must Have):
        - {', '.join(gaps['critical_gaps']) if gaps['critical_gaps'] else 'None'}
        
        Important Gaps (Strongly Preferred):
        - {', '.join(gaps['important_gaps']) if gaps['important_gaps'] else 'None'}
        
        Nice-to-Have Gaps:
        - {', '.join(gaps['nice_to_have_gaps']) if gaps['nice_to_have_gaps'] else 'None'}
        
        Your Current Skills: {len(gaps['user_skills_explicit'])}
        + Implicit Skills (inherited): {len(gaps['implicit_skills'])}
        = Total Effective Skills: {len(gaps['user_skills_with_implicit'])}
        """
        return summary
