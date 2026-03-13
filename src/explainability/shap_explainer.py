"""
Phase 5: SHAP Explainability System
Explains why jobs match using SHAP values
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import shap
import sys
import os

sys.path.append('..')
from matching.ranker import rank_jobs_for_resume

class JobMatchExplainer:
    """Explains job matches using SHAP"""
    
    def __init__(self):
        self.model = None
        self.explainer = None
        self.feature_names = None
        self.skill_vocab = None
    
    def prepare_training_data(self, resumes_df, jobs_df, num_samples=1000):
        """
        Create training dataset for explainability model
        
        For each resume, sample positive (high match) and negative (low match) jobs
        """
        print("📊 Preparing training data for explainability...")
        
        # Load skill vocabulary
        skill_vocab_df = pd.read_csv('data/processed/skills_vocabulary.csv')
        self.skill_vocab = skill_vocab_df['skill'].tolist()
        
        training_data = []
        
        # Sample resumes
        sample_resumes = resumes_df.sample(n=min(num_samples, len(resumes_df)), random_state=42)
        
        for idx, resume in sample_resumes.iterrows():
            resume_skills = [s.strip() for s in str(resume['skills']).split(',')]
            
            # Get matches
            matches = rank_jobs_for_resume(resume['skills'], jobs_df, top_n=50, min_score=0)
            
            if not matches:
                continue
            
            # Sample positive (top matches)
            for match in matches[:5]:
                features = self._create_features(resume_skills, match)
                features['is_good_match'] = 1 if match['score'] >= 50 else 0
                training_data.append(features)
            
            # Sample negative (low matches)
            for match in matches[-5:]:
                features = self._create_features(resume_skills, match)
                features['is_good_match'] = 1 if match['score'] >= 50 else 0
                training_data.append(features)
        
        df = pd.DataFrame(training_data)
        print(f"  ✓ Created {len(df)} training samples")
        print(f"  ✓ Positive samples: {df['is_good_match'].sum()}")
        print(f"  ✓ Negative samples: {len(df) - df['is_good_match'].sum()}")
        
        return df
    
    def _create_features(self, resume_skills, job_match):
        """Create feature vector for a resume-job pair"""
        features = {}
        
        # Basic match features
        features['match_score'] = job_match['score']
        features['required_match_pct'] = job_match['details']['required_percent']
        features['preferred_match_pct'] = job_match['details']['preferred_percent']
        features['num_matched_skills'] = len(job_match['details']['matched_required']) + len(job_match['details']['matched_preferred'])
        features['num_missing_required'] = len(job_match['details']['missing_required'])
        
        # Job characteristics
        features['remote_allowed'] = job_match.get('remote_allowed', 0)
        features['has_salary'] = 1 if pd.notna(job_match.get('normalized_salary')) else 0
        
        # Skill presence features (top 20 most common skills)
        top_skills = self.skill_vocab[:20] if self.skill_vocab else []
        for skill in top_skills:
            features[f'has_{skill.replace(" ", "_").lower()}'] = 1 if skill in resume_skills else 0
        
        return features
    
    def train_explainer(self, training_df):
        """Train Random Forest model for SHAP explainability"""
        print("\n🎓 Training explainability model...")
        
        # Prepare X and y
        y = training_df['is_good_match']
        X = training_df.drop('is_good_match', axis=1)
        
        self.feature_names = X.columns.tolist()
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train Random Forest
        self.model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
        self.model.fit(X_train, y_train)
        
        # Evaluate
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)
        
        print(f"  ✓ Train accuracy: {train_score:.2%}")
        print(f"  ✓ Test accuracy: {test_score:.2%}")
        
        # Create SHAP explainer
        print("\n🔍 Initializing SHAP explainer...")
        self.explainer = shap.TreeExplainer(self.model)
        print("  ✓ SHAP explainer ready")
        
        return test_score
    
    def explain_match(self, resume_skills, job_match):
        """Explain why a job matches using SHAP values"""
        if self.model is None or self.explainer is None:
            raise ValueError("Model not trained. Call train_explainer() first.")
        
        # Create features
        features = self._create_features(resume_skills, job_match)
        
        # Convert to DataFrame
        X = pd.DataFrame([features])
        
        # Ensure all training features are present
        for col in self.feature_names:
            if col not in X.columns:
                X[col] = 0
        X = X[self.feature_names]
        
        # Get SHAP values
        shap_values = self.explainer.shap_values(X)
        
        # Get top contributing features
        if isinstance(shap_values, list):
            shap_values = shap_values[1]  # For binary classification
        
        feature_importance = list(zip(self.feature_names, shap_values[0]))
        feature_importance.sort(key=lambda x: abs(x[1]), reverse=True)
        
        return {
            'top_positive': [(f, v) for f, v in feature_importance if v > 0][:5],
            'top_negative': [(f, v) for f, v in feature_importance if v < 0][:5],
            'base_value': self.explainer.expected_value,
            'prediction': self.model.predict_proba(X)[0][1]
        }
    
    def explain_top_matches(self, resume_skills, jobs_df, top_n=5):
        """Get explanations for top N matches"""
        print(f"\n🔍 Finding and explaining top {top_n} matches...")
        
        # Get matches
        matches = rank_jobs_for_resume(resume_skills, jobs_df, top_n=top_n, min_score=0)
        
        explanations = []
        for i, match in enumerate(matches, 1):
            print(f"\nJob {i}: {match['title']} (Match: {match['score']:.1f}%)")
            
            explanation = self.explain_match(resume_skills.split(','), match)
            
            print("  Top reasons FOR this match:")
            for feature, value in explanation['top_positive']:
                print(f"    • {feature}: +{value:.3f}")
            
            print("  Top reasons AGAINST this match:")
            for feature, value in explanation['top_negative']:
                print(f"    • {feature}: {value:.3f}")
            
            explanations.append({
                'job_title': match['title'],
                'match_score': match['score'],
                'explanation': explanation
            })
        
        return explanations

def build_explainability_system():
    """Complete pipeline to build SHAP explainability"""
    print("=" * 70)
    print("🎯 PHASE 5: SHAP EXPLAINABILITY SYSTEM")
    print("=" * 70)
    print()
    
    # Load data
    print("📂 Loading data...")
    jobs_df = pd.read_csv('data/processed/jobs_parsed.csv')
    resumes_df = pd.read_csv('data/processed/resume_skills.csv')
    resumes_df = resumes_df[resumes_df['skills'].notna()].reset_index(drop=True)
    
    print(f"  ✓ {len(jobs_df):,} jobs")
    print(f"  ✓ {len(resumes_df):,} resumes")
    
    # Initialize explainer
    explainer = JobMatchExplainer()
    
    # Prepare training data
    training_df = explainer.prepare_training_data(resumes_df, jobs_df, num_samples=500)
    
    # Train
    accuracy = explainer.train_explainer(training_df)
    
    # Test on sample resume
    print("\n" + "=" * 70)
    print("📝 DEMO: Explaining matches for sample resume")
    print("=" * 70)
    
    sample_resume = resumes_df.iloc[0]
    print(f"\nResume Category: {sample_resume['category']}")
    print(f"Resume Skills: {sample_resume['skills']}")
    
    explanations = explainer.explain_top_matches(sample_resume['skills'], jobs_df, top_n=3)
    
    print("\n" + "=" * 70)
    print("✅ EXPLAINABILITY SYSTEM READY")
    print("=" * 70)
    print()
    print(f"Model Accuracy: {accuracy:.1%}")
    print("SHAP values available for all matches")
    print()
    
    return explainer

if __name__ == "__main__":
    explainer = build_explainability_system()
