#!/usr/bin/env python3
"""
Quick staging smoke test runner
Sets ENV=staging and runs the staging smoke test
"""
import os
import subprocess
import sys

def main():
    # Set staging environment
    env = os.environ.copy()
    env['ENV'] = 'staging'
    env['ENABLE_SMOKE_TESTS'] = 'true'
    env['ENABLE_DEBUG_LOGGING'] = 'true'
    
    print("🚀 Running staging smoke test with ENV=staging")
    
    # Run the staging smoke test
    result = subprocess.run(
        [sys.executable, 'tests/smoke/test_staging_smoke.py'],
        env=env,
        cwd=os.path.dirname(__file__)
    )
    
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
