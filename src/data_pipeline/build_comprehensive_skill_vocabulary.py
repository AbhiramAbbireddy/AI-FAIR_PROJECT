"""
Comprehensive Skill Vocabulary Builder
Combines skills from multiple sources:
1. O*NET Skills and Knowledge taxonomy
2. Skills extracted from job postings
3. Manually curated technical skills list
"""

import pandas as pd
import re
from collections import Counter

def load_onet_skills():
    """Load skills from O*NET taxonomy"""
    print("📚 Loading O*NET taxonomy...")
    
    skills_path = "data/raw/skills/Skills.txt"
    knowledge_path = "data/raw/skills/Knowledge.txt"
    
    try:
        skills_df = pd.read_csv(skills_path, sep="\t", encoding='utf-8', on_bad_lines='skip')
        knowledge_df = pd.read_csv(knowledge_path, sep="\t", encoding='utf-8', on_bad_lines='skip')
        
        skills = skills_df["Element Name"].dropna().str.strip().str.lower().unique()
        knowledge = knowledge_df["Element Name"].dropna().str.strip().str.lower().unique()
        
        onet_skills = list(set(skills) | set(knowledge))
        print(f"  ✓ Extracted {len(onet_skills)} skills from O*NET")
        return onet_skills
    
    except Exception as e:
        print(f"  ⚠ Warning: Could not load O*NET files - {e}")
        return []


def extract_skills_from_jobs():
    """Extract common skills from job postings"""
    print("💼 Extracting skills from job postings...")
    
    try:
        # Load job skills mapping if it exists
        job_skills_path = "data/raw/jobs/jobs/job_skills.csv"
        df = pd.read_csv(job_skills_path)
        
        if 'skill_abr' in df.columns:
            skills = df['skill_abr'].dropna().str.lower().str.strip().unique()
            print(f"  ✓ Extracted {len(skills)} skills from job postings")
            return list(skills)
        else:
            print("  ⚠ No skill column found in job_skills.csv")
            return []
            
    except Exception as e:
        print(f"  ⚠ Warning: Could not load job skills - {e}")
        return []


def get_curated_technical_skills():
    """Manually curated list of important technical and professional skills"""
    print("🛠️  Loading curated technical skills...")
    
    skills = {
        # Programming Languages
        "python", "java", "javascript", "typescript", "c++", "c#", "c", "php", 
        "ruby", "swift", "kotlin", "go", "rust", "scala", "r", "matlab", "perl",
        
        # Web Technologies
        "html", "css", "html5", "css3", "xml", "json", "rest api", "graphql",
        "soap", "websocket", "ajax",
        
        # Frontend Frameworks
        "react", "angular", "vue.js", "vue", "jquery", "bootstrap", "tailwind css",
        "sass", "less", "webpack", "redux", "next.js", "svelte",
        
        # Backend Frameworks
        "node.js", "express.js", "django", "flask", "spring boot", "spring", 
        ".net", "asp.net", "ruby on rails", "laravel", "fastapi",
        
        # Databases
        "sql", "mysql", "postgresql", "mongodb", "redis", "oracle", "sql server",
        "sqlite", "cassandra", "elasticsearch", "dynamodb", "firebase",
        
        # Cloud & DevOps
        "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "jenkins",
        "ci/cd", "devops", "terraform", "ansible", "git", "github", "gitlab",
        "bitbucket", "linux", "unix", "bash", "shell scripting",
        
        # Data Science & ML
        "machine learning", "deep learning", "artificial intelligence", "ai",
        "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
        "data analysis", "data science", "statistics", "nlp", "computer vision",
        "neural networks", "data mining", "big data", "hadoop", "spark",
        
        # Data Visualization
        "tableau", "power bi", "matplotlib", "seaborn", "d3.js", "plotly",
        
        # Testing
        "unit testing", "integration testing", "test automation", "junit",
        "pytest", "selenium", "jest", "cypress", "tdd", "bdd",
        
        # Methodologies
        "agile", "scrum", "kanban", "waterfall", "lean", "six sigma",
        
        # Architecture
        "microservices", "system design", "api design", "software architecture",
        "design patterns", "object-oriented programming", "oop", "functional programming",
        
        # Security
        "cybersecurity", "information security", "penetration testing", "encryption",
        "oauth", "jwt", "ssl", "tls",
        
        # Mobile Development
        "android", "ios", "react native", "flutter", "mobile development",
        
        # Project Management
        "project management", "jira", "confluence", "asana", "trello",
        "monday.com", "ms project",
        
        # Microsoft Office
        "excel", "word", "powerpoint", "microsoft office", "outlook",
        "google workspace", "google sheets",
        
        # Soft Skills
        "problem solving", "critical thinking", "communication", "teamwork",
        "leadership", "collaboration", "time management", "analytical thinking",
        "creativity", "adaptability", "attention to detail", "decision making",
        
        # Business Skills
        "business analysis", "requirements gathering", "stakeholder management",
        "strategic planning", "business intelligence", "data-driven decision making",
        
        # Other Technical
        "api", "version control", "debugging", "code review", "documentation",
        "technical writing", "performance optimization", "troubleshooting",
        "networking", "tcp/ip", "dns", "http", "https"
    }
    
    print(f"  ✓ Loaded {len(skills)} curated technical skills")
    return list(skills)


def clean_and_normalize_skills(skills_list):
    """Clean, normalize, and deduplicate skills"""
    print("🧹 Cleaning and normalizing skills...")
    
    cleaned_skills = set()
    
    for skill in skills_list:
        if pd.isna(skill) or not skill:
            continue
            
        skill = str(skill).lower().strip()
        
        # Remove special characters but keep meaningful ones like + and #
        # C++ and C# should remain intact
        skill = re.sub(r'[^\w\s\+\#\.\-]', '', skill)
        
        # Remove extra whitespace
        skill = ' '.join(skill.split())
        
        # Skip very short skills (likely noise)
        if len(skill) >= 2:
            cleaned_skills.add(skill)
    
    print(f"  ✓ Cleaned {len(cleaned_skills)} unique skills")
    return sorted(list(cleaned_skills))


def main():
    print("=" * 70)
    print("🎯 COMPREHENSIVE SKILLS VOCABULARY BUILDER")
    print("=" * 70)
    print()
    
    # Collect skills from all sources
    all_skills = []
    
    # Source 1: O*NET taxonomy
    onet_skills = load_onet_skills()
    all_skills.extend(onet_skills)
    
    # Source 2: Job postings
    job_skills = extract_skills_from_jobs()
    all_skills.extend(job_skills)
    
    # Source 3: Curated technical skills
    technical_skills = get_curated_technical_skills()
    all_skills.extend(technical_skills)
    
    print()
    print(f"📊 Total skills collected: {len(all_skills)}")
    print()
    
    # Clean and deduplicate
    final_skills = clean_and_normalize_skills(all_skills)
    
    # Save to CSV
    vocab_df = pd.DataFrame(final_skills, columns=["skill"])
    vocab_df.to_csv("data/processed/skills_vocabulary.csv", index=False)
    
    print()
    print("=" * 70)
    print(f"✅ SUCCESS! Final vocabulary size: {len(vocab_df)}")
    print(f"✅ Saved to: data/processed/skills_vocabulary.csv")
    print("=" * 70)
    print()
    print("📋 Sample skills:")
    for i, skill in enumerate(vocab_df.head(20)["skill"], 1):
        print(f"  {i:2d}. {skill}")
    
    # Statistics
    print()
    print("📈 Vocabulary Statistics:")
    print(f"  • Multi-word skills: {len([s for s in final_skills if ' ' in s])}")
    print(f"  • Single-word skills: {len([s for s in final_skills if ' ' not in s])}")
    print(f"  • Skills with special chars: {len([s for s in final_skills if any(c in s for c in ['+', '#', '.'])])}")


if __name__ == "__main__":
    main()
