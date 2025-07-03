#!/usr/bin/env python3
"""
Remove API Keys Script

Removes specific Google API key lines from Walmart raw data files while preserving all other content.
"""

import os
import re
import glob

def remove_api_keys_from_file(filepath):
    """Remove API key lines from a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Remove the specific API key lines
        patterns_to_remove = [
            r'^\s*"checkAddressAPIKey":\s*"[^"]*",?\s*$',
            r'^\s*"addressAPIKey":\s*"[^"]*",?\s*$', 
            r'^\s*"geoCodingAPIKey":\s*"[^"]*",?\s*$',
            r'^\s*"riseMapAPIKey":\s*\{[^}]*\},?\s*$'
        ]
        
        lines = content.split('\n')
        filtered_lines = []
        skip_next_lines = 0
        
        for i, line in enumerate(lines):
            # Check if this line matches any API key pattern
            should_remove = False
            
            for pattern in patterns_to_remove:
                if re.match(pattern, line, re.MULTILINE):
                    should_remove = True
                    break
            
            # Special handling for riseMapAPIKey object
            if '"riseMapAPIKey"' in line and '{' in line:
                should_remove = True
                # Count how many lines to skip for the object
                brace_count = line.count('{') - line.count('}')
                j = i + 1
                while j < len(lines) and brace_count > 0:
                    next_line = lines[j]
                    brace_count += next_line.count('{') - next_line.count('}')
                    skip_next_lines += 1
                    j += 1
            
            if skip_next_lines > 0:
                skip_next_lines -= 1
                continue
                
            if not should_remove:
                filtered_lines.append(line)
        
        new_content = '\n'.join(filtered_lines)
        
        # Only write if content changed
        if new_content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """Remove API keys from all Walmart raw data files."""
    print("🔒 REMOVING API KEYS FROM WALMART FILES")
    print("=" * 50)
    
    # Get all files in raw/walmart directory
    walmart_files = glob.glob("raw/walmart/*")
    
    if not walmart_files:
        print("❌ No Walmart files found in raw/walmart/")
        return
    
    print(f"📁 Found {len(walmart_files)} files to process")
    
    modified_count = 0
    
    for filepath in walmart_files:
        if os.path.isfile(filepath):
            print(f"🔍 Processing: {os.path.basename(filepath)}")
            
            if remove_api_keys_from_file(filepath):
                print(f"   ✅ Removed API keys")
                modified_count += 1
            else:
                print(f"   ⚪ No changes needed")
    
    print(f"\n🎉 COMPLETED!")
    print(f"   📝 Files processed: {len(walmart_files)}")
    print(f"   ✅ Files modified: {modified_count}")
    print(f"   🔒 API keys removed from all files")

if __name__ == "__main__":
    main()
