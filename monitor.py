"""
System Monitoring Dashboard
Real-time monitoring of FAIR-PATH system health
"""

import pandas as pd
import sys
import os
from datetime import datetime
import time

def check_system_health():
    """Comprehensive system health check"""
    print("\n" + "="*70)
    print("🏥 FAIR-PATH SYSTEM HEALTH CHECK")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    health_status = {
        'overall': 'HEALTHY',
        'warnings': [],
        'errors': []
    }
    
    # 1. Check data files
    print("📂 Data Files:")
    print("-" * 70)
    
    data_files = {
        'Skills Vocabulary': 'data/processed/skills_vocabulary.csv',
        'Resume Skills': 'data/processed/resume_skills.csv',
        'Parsed Jobs': 'data/processed/jobs_parsed.csv',
        'Skill Trends': 'data/processed/skill_trends.csv',
        'Category Trends': 'data/processed/category_trends.csv'
    }
    
    for name, path in data_files.items():
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                size_mb = os.path.getsize(path) / (1024 * 1024)
                print(f"  ✅ {name:20} | {len(df):8,} rows | {size_mb:6.2f} MB")
            except Exception as e:
                print(f"  ⚠️  {name:20} | Error reading: {str(e)}")
                health_status['warnings'].append(f"{name} corrupted")
        else:
            status = "❌" if 'Trends' not in name else "⚠️"
            print(f"  {status} {name:20} | Not found")
            if 'Trends' not in name:
                health_status['errors'].append(f"{name} missing")
    
    print()
    
    # 2. Check processing status
    print("⚙️  Processing Status:")
    print("-" * 70)
    
    if os.path.exists('data/processed/resume_skills.csv'):
        resume_df = pd.read_csv('data/processed/resume_skills.csv')
        with_skills = resume_df['skills'].notna().sum()
        success_rate = (with_skills / len(resume_df)) * 100
        
        status_icon = "✅" if success_rate >= 95 else "⚠️" if success_rate >= 80 else "❌"
        print(f"  {status_icon} Resume Extraction: {success_rate:.1f}% ({with_skills:,}/{len(resume_df):,})")
        
        if success_rate < 95:
            health_status['warnings'].append(f"Low resume success rate: {success_rate:.1f}%")
    
    if os.path.exists('data/processed/jobs_parsed.csv'):
        jobs_df = pd.read_csv('data/processed/jobs_parsed.csv')
        total_expected = 123849
        progress = (len(jobs_df) / total_expected) * 100
        
        if progress >= 100:
            print(f"  ✅ Job Parsing: Complete ({len(jobs_df):,} jobs)")
        else:
            print(f"  🔄 Job Parsing: {progress:.1f}% ({len(jobs_df):,}/{total_expected:,})")
            health_status['warnings'].append(f"Job parsing incomplete: {progress:.1f}%")
    
    print()
    
    # 3. Check logs
    print("📝 Recent Logs:")
    print("-" * 70)
    
    log_dir = 'logs'
    if os.path.exists(log_dir):
        log_files = [f for f in os.listdir(log_dir) if f.endswith('.log') or f.endswith('.csv')]
        
        if log_files:
            for log_file in sorted(log_files)[-5:]:  # Last 5 logs
                log_path = os.path.join(log_dir, log_file)
                size_kb = os.path.getsize(log_path) / 1024
                mod_time = datetime.fromtimestamp(os.path.getmtime(log_path))
                print(f"  📄 {log_file:40} | {size_kb:6.1f} KB | {mod_time.strftime('%Y-%m-%d %H:%M')}")
            
            # Check for recent errors
            error_log = os.path.join(log_dir, 'error_log.csv')
            if os.path.exists(error_log):
                error_df = pd.read_csv(error_log)
                recent_errors = error_df[pd.to_datetime(error_df['timestamp']) > datetime.now() - pd.Timedelta(hours=24)]
                
                if len(recent_errors) > 0:
                    print(f"\n  ⚠️  {len(recent_errors)} errors in last 24 hours")
                    health_status['warnings'].append(f"{len(recent_errors)} recent errors")
        else:
            print("  📝 No logs found")
    else:
        print("  📝 Log directory not found")
    
    print()
    
    # 4. Check disk space
    print("💾 Disk Usage:")
    print("-" * 70)
    
    total_size = 0
    for root, dirs, files in os.walk('.'):
        for file in files:
            try:
                total_size += os.path.getsize(os.path.join(root, file))
            except:
                pass
    
    total_gb = total_size / (1024**3)
    print(f"  Project size: {total_gb:.2f} GB")
    
    if total_gb > 10:
        health_status['warnings'].append(f"Large project size: {total_gb:.2f} GB")
    
    print()
    
    # 5. Overall status
    print("="*70)
    if health_status['errors']:
        print("❌ SYSTEM STATUS: UNHEALTHY")
        print("\nErrors:")
        for error in health_status['errors']:
            print(f"  • {error}")
    elif health_status['warnings']:
        print("⚠️  SYSTEM STATUS: WARNING")
        print("\nWarnings:")
        for warning in health_status['warnings']:
            print(f"  • {warning}")
    else:
        print("✅ SYSTEM STATUS: HEALTHY")
    
    print("="*70)
    print()
    
    return health_status

def monitor_continuously(interval_seconds=30):
    """Continuous monitoring with auto-refresh"""
    print("🔄 Starting continuous monitoring...")
    print(f"Refresh interval: {interval_seconds} seconds")
    print("Press Ctrl+C to stop")
    print()
    
    try:
        while True:
            check_system_health()
            print(f"\nNext check in {interval_seconds} seconds...")
            time.sleep(interval_seconds)
            
            # Clear screen (works on Windows/Linux)
            os.system('cls' if os.name == 'nt' else 'clear')
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitoring stopped")

if __name__ == "__main__":
    if '--continuous' in sys.argv:
        interval = 30
        if '--interval' in sys.argv:
            idx = sys.argv.index('--interval')
            interval = int(sys.argv[idx + 1])
        
        monitor_continuously(interval)
    else:
        check_system_health()
        
        # Offer continuous mode
        print("💡 Tip: Run with --continuous flag for auto-refresh monitoring")
        print("   Example: python monitor.py --continuous --interval 60")
        print()
