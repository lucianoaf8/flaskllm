#!/usr/bin/env python3

'''
Test runner script to diagnose import issues.
'''
import sys
import traceback

# File paths to test
files_to_test = [
    'tests/unit/test_error_handling.py',
    'tests/unit/test_rate_limiter.py',
    'tests/unit/test_templates.py',
    'tests/integration/test_api_advanced.py'
]

def test_import(file_path):
    print(f"\nTesting import of {file_path}...")
    try:
        # Attempt to import the module
        module_path = file_path.replace('/', '.').replace('.py', '')
        __import__(module_path)
        print(f"✅ Successfully imported {file_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to import {file_path}: {e}")
        traceback.print_exc()
        return False

def main():
    success_count = 0
    for file_path in files_to_test:
        if test_import(file_path):
            success_count += 1
    
    print(f"\nSummary: {success_count}/{len(files_to_test)} imports successful")
    return 0 if success_count == len(files_to_test) else 1

if __name__ == '__main__':
    sys.exit(main())
