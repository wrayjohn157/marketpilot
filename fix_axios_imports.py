#!/usr/bin/env python3
"""
Fix axios imports by replacing with fetch API
"""

import os
import re
from pathlib import Path

def fix_axios_in_file(file_path):
    """Replace axios usage with fetch API in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Remove axios import
        content = re.sub(r'import axios from ["\']axios["\'];?\n?', '', content)
        content = re.sub(r'import \* as axios from ["\']axios["\'];?\n?', '', content)
        
        # Replace axios.get calls
        content = re.sub(
            r'axios\.get\(([^)]+)\)',
            r'fetch(\1).then(res => res.json())',
            content
        )
        
        # Replace axios.post calls
        content = re.sub(
            r'axios\.post\(([^,]+),\s*([^)]+)\)',
            r'fetch(\1, {\n      method: "POST",\n      headers: {\n        "Content-Type": "application/json",\n      },\n      body: JSON.stringify(\2)\n    }).then(res => res.json())',
            content
        )
        
        # Replace axios.put calls
        content = re.sub(
            r'axios\.put\(([^,]+),\s*([^)]+)\)',
            r'fetch(\1, {\n      method: "PUT",\n      headers: {\n        "Content-Type": "application/json",\n      },\n      body: JSON.stringify(\2)\n    }).then(res => res.json())',
            content
        )
        
        # Replace axios.delete calls
        content = re.sub(
            r'axios\.delete\(([^)]+)\)',
            r'fetch(\1, {\n      method: "DELETE"\n    }).then(res => res.json())',
            content
        )
        
        # Fix response.data references
        content = re.sub(r'res\.data', 'data', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {file_path}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    """Fix all axios imports in the project"""
    print("🔧 Fixing axios imports...")
    
    # Find all JS/JSX files
    js_files = []
    for root, dirs, files in os.walk("src"):
        for file in files:
            if file.endswith(('.js', '.jsx')):
                js_files.append(Path(root) / file)
    
    fixed_count = 0
    for file_path in js_files:
        if fix_axios_in_file(file_path):
            fixed_count += 1
    
    print(f"✅ Fixed {fixed_count} files")

if __name__ == "__main__":
    main()