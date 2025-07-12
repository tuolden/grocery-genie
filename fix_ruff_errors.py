#!/usr/bin/env python3
"""
Script to automatically fix ruff linting errors
"""

import subprocess
import sys
import os

def run_ruff_fix():
    """Run ruff with automatic fixes"""
    print("🔧 Running ruff with automatic fixes...")
    
    # Run ruff check with --fix flag to automatically fix what it can
    result = subprocess.run([
        "ruff", "check", "src/", "--fix", "--unsafe-fixes"
    ], capture_output=True, text=True, cwd=".")
    
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("Return code:", result.returncode)
    
    # Also run ruff format to fix formatting issues
    print("\n🎨 Running ruff format...")
    format_result = subprocess.run([
        "ruff", "format", "src/"
    ], capture_output=True, text=True, cwd=".")
    
    print("Format STDOUT:", format_result.stdout)
    print("Format STDERR:", format_result.stderr)
    print("Format Return code:", format_result.returncode)
    
    return result.returncode == 0 and format_result.returncode == 0

if __name__ == "__main__":
    success = run_ruff_fix()
    if success:
        print("✅ Ruff fixes applied successfully!")
    else:
        print("❌ Some ruff fixes failed")
        sys.exit(1)
