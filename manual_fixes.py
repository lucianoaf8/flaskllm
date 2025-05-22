#!/usr/bin/env python3
"""
manual_fixes.py - Manual fixes that couldn't be automated
Run this after the diagnostic script to apply remaining fixes.
"""

import os
import sys
from pathlib import Path

def main():
    print("Applying manual fixes...")
    
    # Fix 1: Update all test files to use the new import structure
    fix_test_imports()
    
    # Fix 2: Create missing __init__.py files
    create_init_files()
    
    print("Manual fixes complete!")
    
def fix_test_imports():
    """Update test imports to match new structure."""
    test_dir = Path("tests")
    
    replacements = {
        "from api.v1.schemas import PromptRequest": "from api.v1.schemas.common import PromptRequest",
        "from api.v1.schemas import PromptSource": "from api.v1.schemas.common import PromptSource",
        "from api.v1.schemas import PromptType": "from api.v1.schemas.common import PromptType",
        "from api.v1.schemas import validate_request": "from api.v1.schemas.common import validate_request",
    }
    
    for test_file in test_dir.rglob("*.py"):
        if test_file.is_file():
            content = test_file.read_text()
            modified = False
            
            for old, new in replacements.items():
                if old in content:
                    content = content.replace(old, new)
                    modified = True
                    
            if modified:
                test_file.write_text(content)
                print(f"Updated imports in {test_file}")
                
def create_init_files():
    """Create missing __init__.py files."""
    dirs_needing_init = [
        "api/v1/routes",
        "api/v1/schemas", 
        "core/auth",
        "core/cache",
        "core/errors",
        "core/settings",
        "llm/handlers",
        "llm/storage",
        "llm/utils",
        "utils/config",
        "utils/file_processing",
        "utils/monitoring",
    ]
    
    for dir_path in dirs_needing_init:
        init_file = Path(dir_path) / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created {init_file}")

if __name__ == "__main__":
    main()
