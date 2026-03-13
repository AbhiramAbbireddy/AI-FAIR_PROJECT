#!/usr/bin/env python3
"""
Verify all dependencies and run Streamlit with proper environment
"""
import subprocess
import sys
from pathlib import Path

print("=" * 70)
print("FAIR-PATH STREAMLIT STARTUP")
print("=" * 70)

# Check 1: Python environment
print("\n[1/3] Checking Python environment...")
print(f"  Python: {sys.version}")
print(f"  Executable: {sys.executable}")
print(f"  ✓ Using: {Path(sys.executable).parent.parent.name if Path(sys.executable).parent.parent.name else 'system'}")

# Check 2: Required packages
print("\n[2/3] Checking required packages...")
required_packages = [
    'streamlit',
    'pandas',
    'numpy',
    'google.generativeai',
    'fuzzywuzzy',
    'python_dotenv'
]

missing = []
for pkg in required_packages:
    try:
        __import__(pkg)
        print(f"  ✓ {pkg}")
    except ImportError:
        print(f"  ✗ {pkg} MISSING")
        missing.append(pkg)

if missing:
    print(f"\n  Missing packages: {', '.join(missing)}")
    print(f"  Installing...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)

# Check 3: .env file
print("\n[3/3] Checking .env configuration...")
env_file = Path('.env')
if env_file.exists():
    with open(env_file) as f:
        content = f.read()
        if 'GEMINI_API_KEY' in content:
            print("  ✓ .env file with GEMINI_API_KEY found")
        else:
            print("  ⚠ .env exists but missing GEMINI_API_KEY")
else:
    print("  ⚠ .env file not found")

print("\n" + "=" * 70)
print("Starting Streamlit app...")
print("=" * 70)
print("\nNote: If you see 'No module named google.generativeai' error:")
print("  1. Ctrl+C to stop the app")
print("  2. Run: pip install google-generativeai python-dotenv")
print("  3. Restart the app")
print("\n")

# Start Streamlit
subprocess.run([sys.executable, '-m', 'streamlit', 'run', 'streamlit_app.py'])
