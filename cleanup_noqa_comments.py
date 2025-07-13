#!/usr/bin/env python3
"""
Script to clean up excessive noqa comments now that we have a more focused ruff config
"""

import re
import os
from pathlib import Path

def remove_file_level_noqa_comments():
    """Remove file-level ruff noqa comments that are no longer needed"""
    
    # Find all Python files in src/
    python_files = []
    for root, dirs, files in os.walk("src"):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    
    for file_path in python_files:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Remove file-level ruff noqa comments
        content = re.sub(r'^# ruff: noqa:.*\n', '', content, flags=re.MULTILINE)
        
        # Remove inline noqa comments that are no longer needed with our focused config
        # Keep only essential ones for hardcoded passwords and specific cases
        
        # Remove most inline noqa comments except for essential security ones
        content = re.sub(r'  # noqa: PLR2004', '', content)  # Magic numbers
        content = re.sub(r'  # noqa: PLR0911', '', content)  # Too many returns
        content = re.sub(r'  # noqa: PTH103', '', content)   # Path operations
        content = re.sub(r'  # noqa: PTH208', '', content)   # Path operations
        content = re.sub(r'  # noqa: DTZ007', '', content)   # Timezone naive
        content = re.sub(r'  # noqa: FBT001', '', content)   # Boolean args
        content = re.sub(r'  # noqa: FBT002', '', content)   # Boolean args
        content = re.sub(r'  # noqa: S501', '', content)     # SSL verification
        content = re.sub(r'  # noqa: PLW2901', '', content)  # Loop variable
        content = re.sub(r'  # noqa: N806', '', content)     # Variable naming
        
        # Keep S105 (hardcoded passwords) as they're still important
        # Keep PLC0415 (local imports) as they're still in our config
        
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"✅ Cleaned up noqa comments in {file_path}")
        else:
            print(f"⏭️  No changes needed in {file_path}")

def clean_up_trailing_whitespace():
    """Remove any trailing whitespace that might have been left"""
    
    python_files = []
    for root, dirs, files in os.walk("src"):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    
    for file_path in python_files:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Remove trailing whitespace from each line
        cleaned_lines = [line.rstrip() + '\n' for line in lines]
        
        # Remove the newline from the last line if it's empty
        if cleaned_lines and cleaned_lines[-1].strip() == '':
            cleaned_lines[-1] = cleaned_lines[-1].rstrip()
        
        with open(file_path, 'w') as f:
            f.writelines(cleaned_lines)

if __name__ == "__main__":
    print("🧹 Cleaning up excessive noqa comments...")
    remove_file_level_noqa_comments()
    clean_up_trailing_whitespace()
    print("✅ Cleanup completed!")
