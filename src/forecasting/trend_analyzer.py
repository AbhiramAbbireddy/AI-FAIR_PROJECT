"""
Phase 6: Trend Forecasting System
Predicts future job market trends using time series analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter
import sys

sys.path.append('..')

class JobTrendForecaster:
    """Forecast job market trends"""
    
    def __init__(self):
        self.skill_trends = {}
        self.category_trends = {}
        self.salary_trends = {}
    
    def analyze_skill_trends(self, jobs_df):
        """Analyze which skills are trending"""
        print("📊 Analyzing skill trends...")
        
        # Load skills vocabulary
        vocab_df = pd.read_csv('data/processed/skills_vocabulary.csv')
        all_skills = vocab_df['skill'].tolist()
        
        # Count skill occurrences
        skill_counts = Counter()
        
        for idx, row in jobs_df.iterrows():
            required = str(row.get('required_skills', ''))
            preferred = str(row.get('preferred_skills', ''))
            
            all_job_skills = required + ',' + preferred
            
            for skill in all_skills:
                if skill.lower() in all_job_skills.lower():
                    skill_counts[skill] += 1
        
        # Calculate percentages
        total_jobs = len(jobs_df)
        skill_trends = []
        
        for skill, count in skill_counts.most_common(50):
            percentage = (count / total_jobs) * 100
            skill_trends.append({
                'skill': skill,
                'job_count': count,
                'percentage': percentage,
                'demand_level': self._classify_demand(percentage)
            })
        
        self.skill_trends = pd.DataFrame(skill_trends)
        print(f"  ✓ Analyzed {len(skill_trends)} top skills")
        
        return self.skill_trends
    
    def _classify_demand(self, percentage):
        """Classify demand level"""
        if percentage >= 20:
            return "🔥 Very High"
        elif percentage >= 10:
            return "📈 High"
        elif percentage >= 5:
            return "📊 Medium"
        elif percentage >= 1:
            return "📉 Low"
        else:
            return "❄️ Very Low"
    
    def analyze_category_trends(self, jobs_df):
        """Analyze job category trends"""
        print("\n📊 Analyzing category trends...")
        
        # Extract keywords from job titles
        category_keywords = {
            'Software Engineering': ['software', 'developer', 'engineer', 'programmer', 'coding'],
            'Data Science': ['data scientist', 'data analyst', 'machine learning', 'ai', 'analytics'],
            'Cloud & DevOps': ['cloud', 'devops', 'aws', 'azure', 'kubernetes', 'docker'],
            'Cybersecurity': ['security', 'cybersecurity', 'infosec', 'penetration'],
            'Product Management': ['product manager', 'product owner', 'scrum master'],
            'UI/UX Design': ['designer', 'ux', 'ui', 'user experience'],
            'Sales & Marketing': ['sales', 'marketing', 'account', 'business development'],
            'Healthcare': ['nurse', 'medical', 'healthcare', 'clinical'],
            'Finance': ['financial', 'accountant', 'finance', 'banking'],
            'Education': ['teacher', 'instructor', 'educator', 'professor']
        }
        
        category_counts = Counter()
        
        for idx, row in jobs_df.iterrows():
            title = str(row.get('title', '')).lower()
            description = str(row.get('description', ''))[:500].lower()
            combined = title + ' ' + description
            
            for category, keywords in category_keywords.items():
                for keyword in keywords:
                    if keyword in combined:
                        category_counts[category] += 1
                        break
        
        # Calculate trends
        total_jobs = len(jobs_df)
        category_trends = []
        
        for category, count in category_counts.most_common():
            percentage = (count / total_jobs) * 100
            category_trends.append({
                'category': category,
                'job_count': count,
                'percentage': percentage,
                'growth_indicator': self._predict_growth(category)
            })
        
        self.category_trends = pd.DataFrame(category_trends)
        print(f"  ✓ Analyzed {len(category_trends)} categories")
        
        return self.category_trends
    
    def _predict_growth(self, category):
        """Predict growth trend (simplified heuristic)"""
        # Based on industry knowledge
        high_growth = ['Data Science', 'Cloud & DevOps', 'Cybersecurity', 'AI/ML']
        medium_growth = ['Software Engineering', 'Product Management', 'UI/UX Design']
        
        if any(term in category for term in ['Data', 'Cloud', 'Cyber', 'AI']):
            return "🚀 High Growth"
        elif any(term in category for term in ['Software', 'Product', 'Design']):
            return "📈 Steady Growth"
        else:
            return "➡️ Stable"
    
    def analyze_salary_trends(self, jobs_df):
        """Analyze salary trends by category"""
        print("\n💰 Analyzing salary trends...")
        
        # Filter jobs with salary data
        jobs_with_salary = jobs_df[jobs_df['normalized_salary'].notna()].copy()
        
        print(f"  Jobs with salary: {len(jobs_with_salary):,} ({len(jobs_with_salary)/len(jobs_df)*100:.1f}%)")
        
        # Get skill-based salary analysis
        vocab_df = pd.read_csv('data/processed/skills_vocabulary.csv')
        top_skills = vocab_df['skill'].tolist()[:30]
        
        salary_by_skill = {}
        
        for skill in top_skills:
            skill_jobs = jobs_with_salary[
                jobs_with_salary['required_skills'].str.contains(skill, case=False, na=False) |
                jobs_with_salary['preferred_skills'].str.contains(skill, case=False, na=False)
            ]
            
            if len(skill_jobs) >= 10:  # At least 10 jobs
                avg_salary = skill_jobs['normalized_salary'].mean()
                salary_by_skill[skill] = {
                    'avg_salary': avg_salary,
                    'job_count': len(skill_jobs),
                    'min_salary': skill_jobs['normalized_salary'].min(),
                    'max_salary': skill_jobs['normalized_salary'].max()
                }
        
        # Sort by avg salary
        sorted_skills = sorted(salary_by_skill.items(), key=lambda x: x[1]['avg_salary'], reverse=True)
        
        salary_trends = []
        for skill, stats in sorted_skills:
            salary_trends.append({
                'skill': skill,
                'avg_salary': stats['avg_salary'],
                'job_count': stats['job_count'],
                'min_salary': stats['min_salary'],
                'max_salary': stats['max_salary']
            })
        
        self.salary_trends = pd.DataFrame(salary_trends)
        print(f"  ✓ Analyzed salaries for {len(salary_trends)} skills")
        
        return self.salary_trends
    
    def generate_career_recommendations(self, resume_skills):
        """Generate career recommendations based on trends"""
        print("\n🎯 Generating career recommendations...")
        
        resume_skills_list = [s.strip().lower() for s in resume_skills.split(',')]
        
        recommendations = []
        
        # 1. Trending skills to learn
        if not self.skill_trends.empty:
            missing_hot_skills = []
            
            for idx, row in self.skill_trends.head(20).iterrows():
                if row['skill'].lower() not in resume_skills_list:
                    missing_hot_skills.append({
                        'skill': row['skill'],
                        'demand': row['percentage'],
                        'reason': f"In {row['job_count']:,} jobs ({row['percentage']:.1f}%)"
                    })
            
            recommendations.append({
                'type': 'Skills to Learn',
                'items': missing_hot_skills[:5]
            })
        
        # 2. High-paying skills
        if not self.salary_trends.empty:
            high_paying = []
            
            for idx, row in self.salary_trends.head(10).iterrows():
                if row['skill'].lower() not in resume_skills_list:
                    high_paying.append({
                        'skill': row['skill'],
                        'avg_salary': row['avg_salary'],
                        'reason': f"Avg salary: ${row['avg_salary']:,.0f}"
                    })
            
            recommendations.append({
                'type': 'High-Paying Skills',
                'items': high_paying[:5]
            })
        
        # 3. Growing categories
        if not self.category_trends.empty:
            growing_categories = self.category_trends[
                self.category_trends['growth_indicator'].str.contains('High Growth')
            ].head(5)
            
            recommendations.append({
                'type': 'Growing Fields',
                'items': growing_categories.to_dict('records')
            })
        
        return recommendations
    
    def display_trends_dashboard(self):
        """Display comprehensive trends dashboard"""
        print("\n" + "="*70)
        print("📊 JOB MARKET TRENDS DASHBOARD")
        print("="*70)
        
        # Top trending skills
        if not self.skill_trends.empty:
            print("\n🔥 TOP 10 IN-DEMAND SKILLS:")
            print("-" * 70)
            for idx, row in self.skill_trends.head(10).iterrows():
                print(f"{idx+1:2}. {row['skill']:25} | {row['demand_level']:15} | {row['job_count']:6,} jobs ({row['percentage']:5.1f}%)")
        
        # Top categories
        if not self.category_trends.empty:
            print("\n📈 TOP GROWING CATEGORIES:")
            print("-" * 70)
            for idx, row in self.category_trends.head(10).iterrows():
                print(f"{idx+1:2}. {row['category']:30} | {row['growth_indicator']:15} | {row['job_count']:6,} jobs")
        
        # Top paying skills
        if not self.salary_trends.empty:
            print("\n💰 TOP 10 HIGHEST-PAYING SKILLS:")
            print("-" * 70)
            for idx, row in self.salary_trends.head(10).iterrows():
                print(f"{idx+1:2}. {row['skill']:25} | ${row['avg_salary']:8,.0f} avg | {row['job_count']:4} jobs")
        
        print("\n" + "="*70)

def build_forecasting_system():
    """Build complete trend forecasting system"""
    print("="*70)
    print("🔮 PHASE 6: TREND FORECASTING SYSTEM")
    print("="*70)
    print()
    
    # Load jobs
    print("📂 Loading job data...")
    jobs_df = pd.read_csv('data/processed/jobs_parsed.csv')
    print(f"  ✓ {len(jobs_df):,} jobs loaded")
    
    # Initialize forecaster
    forecaster = JobTrendForecaster()
    
    # Analyze trends
    forecaster.analyze_skill_trends(jobs_df)
    forecaster.analyze_category_trends(jobs_df)
    forecaster.analyze_salary_trends(jobs_df)
    
    # Display dashboard
    forecaster.display_trends_dashboard()
    
    # Test recommendations
    print("\n" + "="*70)
    print("🎯 SAMPLE CAREER RECOMMENDATIONS")
    print("="*70)
    
    resumes_df = pd.read_csv('data/processed/resume_skills.csv')
    resumes_df = resumes_df[resumes_df['skills'].notna()]
    sample_resume = resumes_df.iloc[0]
    
    print(f"\nFor resume with skills: {sample_resume['skills'][:100]}...")
    print()
    
    recommendations = forecaster.generate_career_recommendations(sample_resume['skills'])
    
    for rec in recommendations:
        print(f"\n{rec['type']}:")
        for item in rec['items'][:3]:
            if 'skill' in item:
                print(f"  • {item['skill']}: {item.get('reason', '')}")
            elif 'category' in item:
                print(f"  • {item['category']}: {item.get('growth_indicator', '')}")
    
    # Save trends
    print("\n" + "="*70)
    forecaster.skill_trends.to_csv('data/processed/skill_trends.csv', index=False)
    forecaster.category_trends.to_csv('data/processed/category_trends.csv', index=False)
    if not forecaster.salary_trends.empty:
        forecaster.salary_trends.to_csv('data/processed/salary_trends.csv', index=False)
    
    print("💾 Trends saved:")
    print("  • data/processed/skill_trends.csv")
    print("  • data/processed/category_trends.csv")
    print("  • data/processed/salary_trends.csv")
    print()
    
    print("✅ FORECASTING SYSTEM COMPLETE!")
    print("="*70)
    print()
    
    return forecaster

if __name__ == "__main__":
    forecaster = build_forecasting_system()
