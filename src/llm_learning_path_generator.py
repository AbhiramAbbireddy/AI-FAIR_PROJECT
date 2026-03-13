import os
import json
from dotenv import load_dotenv
from typing import Dict, List, Optional
import time

# Try to import Gemini, but don't fail if not available
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    genai = None

class LLMLearningPathGenerator:
    """Generate personalized learning paths using Google Gemini API"""
    
    def __init__(self):
        """Initialize Gemini API"""
        
        if not HAS_GEMINI:
            raise ImportError(
                "google.generativeai package not found.\n"
                "Install it with: pip install google-generativeai"
            )
        
        load_dotenv()
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "❌ GEMINI_API_KEY not found in .env file.\n"
                "Get your free key at: https://aistudio.google.com/app/apikey\n"
                "Then create .env file with: GEMINI_API_KEY=your_key_here"
            )
        
        genai.configure(api_key=api_key)
        
        # Use Gemini 1.5 Flash (free, fast, good quality)
        self.model = genai.GenerativeModel(
            'gemini-1.5-flash',
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "max_output_tokens": 8192,
            }
        )
        
        print("✓ Gemini API initialized successfully")
    
    def generate_learning_path(
        self,
        user_skills: List[str],
        missing_skills: List[Dict],
        job_title: str,
        job_description: str,
        current_match_score: float,
        user_context: Optional[Dict] = None
    ) -> Dict:
        """
        Generate personalized learning path using Gemini API
        
        Args:
            user_skills: List of skills user currently has
            missing_skills: List of skills user needs to learn (with priorities)
            job_title: Target job title
            job_description: Full job description
            current_match_score: Current match percentage
            user_context: Optional dict with user preferences
        
        Returns:
            Dict with structured learning path
        """
        
        # Build the prompt
        prompt = self._build_learning_path_prompt(
            user_skills,
            missing_skills,
            job_title,
            job_description,
            current_match_score,
            user_context or {}
        )
        
        try:
            print(f"🔄 Generating personalized learning path for {job_title}...")
            
            # Call Gemini API with retry
            response = self._call_gemini_with_retry(prompt, max_retries=3)
            
            # Parse JSON response
            learning_path = self._parse_gemini_response(response)
            
            # Validate structure
            validated_path = self._validate_learning_path(learning_path)
            
            print("✓ Learning path generated successfully")
            return validated_path
            
        except Exception as e:
            print(f"⚠ Error generating learning path: {e}")
            print("  Using fallback learning path...")
            return self._fallback_learning_path(missing_skills, job_title)
    
    def _call_gemini_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """Call Gemini API with retry logic"""
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                print(f"  Attempt {attempt + 1} failed: {e}")
                print(f"  Retrying in 2 seconds...")
                time.sleep(2)
    
    def _build_learning_path_prompt(
        self,
        user_skills: List[str],
        missing_skills: List[Dict],
        job_title: str,
        job_description: str,
        current_match_score: float,
        user_context: Dict
    ) -> str:
        """Build structured prompt for Gemini"""
        
        experience = user_context.get("experience_level", "intermediate")
        time_available = user_context.get("available_time", "part-time")
        learning_style = user_context.get("learning_style", "hands-on")
        budget = user_context.get("budget", "budget-friendly")
        
        # Format missing skills
        skills_text = "\n".join([
            f"- {skill['skill']} (Priority: {skill.get('priority_score', 0)}/100, Category: {skill.get('category', 'OTHER')})"
            for skill in missing_skills[:10]
        ])
        
        prompt = f"""You are an expert career advisor creating a detailed, personalized learning roadmap.

USER PROFILE:
- Current Skills: {', '.join(user_skills) if user_skills else 'None specified'}
- Experience Level: {experience}
- Time Available: {time_available}
- Learning Style: {learning_style}
- Budget: {budget}
- Current Match Score for Target Role: {current_match_score}%

TARGET JOB:
- Job Title: {job_title}
- Job Description: {job_description[:500] if job_description else 'No description provided'}...

SKILLS TO LEARN (Priority Ranked):
{skills_text}

TASK: Create a detailed, month-by-month learning roadmap.

CRITICAL REQUIREMENTS:
1. Return ONLY valid JSON - no markdown, no explanation
2. Include specific resource names (actual courses, books, communities)
3. Check for prerequisites - include them if user lacks them
4. Mix quick wins (easy, high-impact) with long-term investments
5. Be specific about timelines based on {time_available}
6. Realistic for {experience} level learners

OUTPUT: Return ONLY this JSON structure (fill all fields):

{{
  "learning_path": {{
    "initial_match_score": {current_match_score},
    "target_match_score": 90,
    "total_duration_months": 6,
    "estimated_hours_total": 200,
    
    "phases": [
      {{
        "phase_number": 1,
        "phase_name": "Foundation",
        "duration_months": 2,
        "skills_covered": ["Skill1", "Skill2"],
        "match_score_after": 75
      }}
    ],
    
    "milestones": [
      {{
        "month": 1,
        "week_range": "1-4",
        "skill": "Skill Name",
        "category": "CRITICAL",
        "priority_score": 85,
        "learning_objectives": ["Objective 1", "Objective 2"],
        "resources": [
          {{
            "type": "course",
            "name": "Specific Course Name",
            "platform": "Platform Name",
            "duration": "4 hours",
            "cost": "free"
          }}
        ],
        "practice_projects": ["Project 1", "Project 2"],
        "estimated_hours_per_week": 8,
        "difficulty": "easy",
        "match_score_after": 78,
        "score_improvement": 3,
        "success_criteria": ["Criteria 1", "Criteria 2"]
      }}
    ],
    
    "quick_wins": [
      {{
        "skill": "Skill",
        "why_quick_win": "Reason",
        "time_needed": "2 weeks",
        "impact": "Impact description"
      }}
    ],
    
    "long_term_investments": [
      {{
        "skill": "Skill",
        "why_important": "Reason",
        "time_needed": "3 months",
        "high_value_because": "Reason"
      }}
    ],
    
    "key_recommendations": [
      "Recommendation 1",
      "Recommendation 2"
    ],
    
    "resource_summary": {{
      "free_resources": 5,
      "paid_resources": 2,
      "total_estimated_cost": "$50",
      "recommended_communities": ["Community 1"]
    }},
    
    "motivation_tips": [
      "Tip 1",
      "Tip 2"
    ]
  }}
}}"""
        
        return prompt
    
    def _parse_gemini_response(self, response_text: str) -> Dict:
        """Parse Gemini's JSON response"""
        
        # Remove markdown code blocks if present
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        try:
            learning_path = json.loads(response_text)
            return learning_path
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Response preview: {response_text[:200]}...")
            raise ValueError(f"Failed to parse Gemini response as JSON")
    
    def _validate_learning_path(self, learning_path: Dict) -> Dict:
        """Validate learning path structure"""
        
        if "learning_path" not in learning_path:
            raise ValueError("Missing 'learning_path' key in response")
        
        path = learning_path["learning_path"]
        
        # Ensure milestones exist
        if "milestones" not in path or not path["milestones"]:
            raise ValueError("Learning path must have at least one milestone")
        
        return learning_path
    
    def _fallback_learning_path(self, missing_skills: List[Dict], job_title: str) -> Dict:
        """Fallback if API fails"""
        
        # Ensure missing_skills is not empty
        if not missing_skills:
            missing_skills = [
                {
                    "skill": f"Develop {job_title} expertise",
                    "category": "CRITICAL",
                    "priority_score": 80
                }
            ]
        
        milestones = []
        
        for i, skill in enumerate(missing_skills[:5], 1):
            skill_name = skill.get("skill", f"Skill {i}") if isinstance(skill, dict) else str(skill)
            category = skill.get("category", "IMPORTANT") if isinstance(skill, dict) else "IMPORTANT"
            priority_score = skill.get("priority_score", 50) if isinstance(skill, dict) else 50
            
            milestones.append({
                "month": i,
                "week_range": f"{(i-1)*4+1}-{i*4}",
                "skill": skill_name,
                "category": category,
                "priority_score": priority_score,
                "learning_objectives": [
                    f"Understand {skill_name} fundamentals",
                    f"Build a small project with {skill_name}"
                ],
                "resources": [
                    {
                        "type": "search",
                        "name": f"Search '{skill_name}' on YouTube/Coursera/Udemy",
                        "platform": "Multiple",
                        "duration": "Variable",
                        "cost": "free/paid"
                    }
                ],
                "practice_projects": [
                    f"Build a project using {skill_name}"
                ],
                "estimated_hours_per_week": 8,
                "difficulty": "moderate",
                "match_score_after": 75 + (i * 3),
                "score_improvement": 3,
                "success_criteria": [
                    f"Understand core concepts of {skill_name}",
                    "Completed at least one project"
                ]
            })
        
        first_skill = missing_skills[0].get("skill", "First skill") if missing_skills and isinstance(missing_skills[0], dict) else "First skill"
        
        return {
            "learning_path": {
                "initial_match_score": 70,
                "target_match_score": 85,
                "total_duration_months": len(milestones),
                "estimated_hours_total": len(milestones) * 32,
                "phases": [],
                "milestones": milestones,
                "quick_wins": [
                    {
                        "skill": first_skill,
                        "why_quick_win": "Start with highest priority",
                        "time_needed": "1-2 weeks",
                        "impact": "Build momentum"
                    }
                ],
                "key_recommendations": [
                    "Search for online courses on platforms like Coursera, Udemy, YouTube",
                    "Join communities and forums for the skills you're learning",
                    "Build projects to gain practical experience",
                    "Connect with mentors in the field"
                ],
                "resource_summary": {
                    "free_resources": 5,
                    "paid_resources": 2,
                    "total_estimated_cost": "varies",
                    "recommended_communities": ["Reddit communities", "Discord servers", "GitHub discussions"]
                },
                "motivation_tips": [
                    "Track progress weekly",
                    "Celebrate small wins",
                    "Join study groups or communities"
                ],
                "error": "Note: Using rule-based learning path. For AI-personalized paths, please set up Gemini API key."
            }
        }
