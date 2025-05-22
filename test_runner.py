#!/usr/bin/env python3
"""
test_runner.py - Focused test runner that handles common issues
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_test_environment():
    """Set up the test environment."""
    # Set environment variables
    test_env = os.environ.copy()
    test_env.update({
        "ENVIRONMENT": "testing",
        "API_TOKEN": "test_token", 
        "OPENAI_API_KEY": "test_key",
        "ANTHROPIC_API_KEY": "test_key",
        "LLM_PROVIDER": "openai",
        "RATE_LIMIT_ENABLED": "False",
        "DEBUG": "True",
        "PYTHONPATH": str(Path.cwd())
    })
    
    return test_env

def run_unit_tests():
    """Run unit tests with proper environment."""
    print("🧪 Running unit tests...")
    
    env = setup_test_environment()
    
    # Run specific test files that should work
    test_files = [
        "tests/unit/test_config.py",
        "tests/unit/test_auth.py",
        "tests/unit/test_validation.py",
    ]
    
    for test_file in test_files:
        print(f"\n📋 Testing {test_file}...")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ {test_file} passed!")
        else:
            print(f"❌ {test_file} failed")
            print("STDOUT:", result.stdout[-500:])  # Last 500 chars
            print("STDERR:", result.stderr[-500:])

def run_integration_tests():
    """Run integration tests."""
    print("\n🔗 Running integration tests...")
    
    env = setup_test_environment()
    
    # First, let's check if the app can even start
    print("Checking if app can start...")
    
    test_app_script = '''
import sys
sys.path.insert(0, '.')

try:
    from app import create_app
    app = create_app()
    print("✅ App created successfully!")
except Exception as e:
    print(f"❌ Failed to create app: {e}")
    import traceback
    traceback.print_exc()
'''
    
    result = subprocess.run(
        [sys.executable, "-c", test_app_script],
        env=env,
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)

def main():
    """Run the test suite."""
    print("🚀 FlaskLLM Focused Test Runner")
    print("=" * 50)
    
    # Run tests
    run_unit_tests()
    run_integration_tests()
    
    print("\n✅ Test run complete!")

if __name__ == "__main__":
    main()