#!/usr/bin/env python3
"""
Script to fix syntax errors from incorrect noqa placement
"""

import re
import os

def fix_syntax_errors():
    """Fix syntax errors caused by incorrect noqa comment placement"""
    
    fixes = [
        # Fix if statements with missing colons
        ("src/scrapers/costco_scraper.py", [
            (r'if response\.status_code == 200  # noqa: PLR2004:', r'if response.status_code == 200:  # noqa: PLR2004'),
            (r'if response\.status_code == 401  # noqa: PLR2004:', r'if response.status_code == 401:  # noqa: PLR2004'),
        ]),
        ("src/scrapers/cvs_scraper.py", [
            (r'if response\.status_code == 200  # noqa: PLR2004:', r'if response.status_code == 200:  # noqa: PLR2004'),
            (r'if access_token == "YOUR_access_token_HERE"  # noqa: S105:', r'if access_token == "YOUR_access_token_HERE":  # noqa: S105'),
        ]),
        ("src/scrapers/publix_detail_scraper.py", [
            (r'if response\.status_code == 200  # noqa: PLR2004:', r'if response.status_code == 200:  # noqa: PLR2004'),
        ]),
        ("src/scrapers/publix_list_scraper.py", [
            (r'if response\.status_code == 200  # noqa: PLR2004:', r'if response.status_code == 200:  # noqa: PLR2004'),
        ]),
    ]
    
    for file_path, patterns in fixes:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)
            
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"✅ Fixed syntax errors in {file_path}")

if __name__ == "__main__":
    print("🔧 Fixing syntax errors...")
    fix_syntax_errors()
    print("✅ Syntax errors fixed!")
