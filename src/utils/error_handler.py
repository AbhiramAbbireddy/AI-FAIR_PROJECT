"""
Production Error Handler
Comprehensive error handling and recovery
"""

import sys
import traceback
import pandas as pd
from functools import wraps
from datetime import datetime

sys.path.append('..')
from utils.logger import error_logger

class FairPathError(Exception):
    """Base exception for FAIR-PATH"""
    pass

class DataNotFoundError(FairPathError):
    """Raised when required data files are missing"""
    pass

class SkillExtractionError(FairPathError):
    """Raised when skill extraction fails"""
    pass

class MatchingError(FairPathError):
    """Raised when matching fails"""
    pass

def safe_execute(default_return=None, raise_on_error=False):
    """
    Decorator for safe execution with error handling
    
    Args:
        default_return: Value to return if error occurs
        raise_on_error: Whether to raise exception after logging
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = f"{func.__name__} failed: {str(e)}"
                error_logger.error(error_msg)
                error_logger.error(traceback.format_exc())
                
                # Log to error report
                log_error_to_file(func.__name__, e)
                
                if raise_on_error:
                    raise
                
                print(f"❌ Error in {func.__name__}: {str(e)}")
                return default_return
        
        return wrapper
    return decorator

def log_error_to_file(function_name, error):
    """Log detailed error information"""
    error_report = {
        'timestamp': datetime.now(),
        'function': function_name,
        'error_type': type(error).__name__,
        'error_message': str(error),
        'traceback': traceback.format_exc()
    }
    
    # Append to error log CSV
    try:
        import os
        os.makedirs('logs', exist_ok=True)
        
        error_df = pd.DataFrame([error_report])
        error_file = 'logs/error_log.csv'
        
        if os.path.exists(error_file):
            existing = pd.read_csv(error_file)
            error_df = pd.concat([existing, error_df], ignore_index=True)
        
        error_df.to_csv(error_file, index=False)
    except:
        pass

def validate_data_files():
    """Validate all required data files exist"""
    required_files = {
        'skills_vocabulary.csv': 'data/processed/skills_vocabulary.csv',
        'resume_skills.csv': 'data/processed/resume_skills.csv',
        'jobs_parsed.csv': 'data/processed/jobs_parsed.csv'
    }
    
    missing = []
    
    for name, path in required_files.items():
        if not pd.io.common.file_exists(path):
            missing.append(name)
    
    if missing:
        error_msg = f"Missing required files: {', '.join(missing)}"
        error_logger.error(error_msg)
        raise DataNotFoundError(error_msg)
    
    return True

def validate_resume_data(resume_skills):
    """Validate resume skills data"""
    if pd.isna(resume_skills) or not resume_skills:
        raise SkillExtractionError("Resume has no skills extracted")
    
    skills_list = [s.strip() for s in str(resume_skills).split(',')]
    
    if len(skills_list) == 0:
        raise SkillExtractionError("Resume skills list is empty")
    
    return skills_list

def validate_job_data(job_row):
    """Validate job data"""
    required_fields = ['title']
    
    for field in required_fields:
        if field not in job_row or pd.isna(job_row[field]):
            raise MatchingError(f"Job missing required field: {field}")
    
    return True

@safe_execute(default_return=[], raise_on_error=False)
def safe_rank_jobs(resume_skills, jobs_df, top_n=20, min_score=0):
    """Safely rank jobs with error handling"""
    from matching.ranker import rank_jobs_for_resume
    
    # Validate inputs
    validate_resume_data(resume_skills)
    
    if jobs_df.empty:
        raise MatchingError("Jobs dataframe is empty")
    
    # Execute matching
    matches = rank_jobs_for_resume(resume_skills, jobs_df, top_n, min_score)
    
    return matches

def handle_parsing_interruption():
    """Handle interrupted job parsing"""
    import os
    
    print("\n⚠️ Checking for interrupted job parsing...")
    
    if not os.path.exists('data/processed/jobs_parsed.csv'):
        print("  No partial data found")
        return False
    
    df = pd.read_csv('data/processed/jobs_parsed.csv')
    total_expected = 123849
    
    if len(df) < total_expected:
        print(f"  Found partial data: {len(df):,}/{total_expected:,} jobs")
        print(f"  Progress: {len(df)/total_expected*100:.1f}%")
        
        response = input("\n  Resume parsing from checkpoint? (y/n): ")
        if response.lower() == 'y':
            return True
    
    return False

if __name__ == "__main__":
    print("🛡️ Error handling system configured")
    
    # Test error handling
    @safe_execute(default_return="fallback")
    def test_function():
        raise ValueError("Test error")
    
    result = test_function()
    print(f"Function returned: {result}")
    
    print("✅ Error handling tested successfully")
