#!/usr/bin/env python3
# comprehensive_validation.py

import importlib
import sys

def test_import(module_path, description):
    try:
        importlib.import_module(module_path)
        print(f"✓ {description}: {module_path}")
        return True
    except ImportError as e:
        print(f"✗ {description}: {module_path} - {e}")
        return False

def main():
    success_count = 0
    total_tests = 0
    
    # Test core imports
    tests = [
        ("core", "Core module"),
        ("core.auth", "Core auth module"), 
        ("core.cache", "Core cache module"),
        ("core.errors", "Core errors module"),
        ("core.settings", "Core settings module"),
        
        # Test API imports
        ("api.v1", "API v1 module"),
        ("api.v1.routes.core", "API core routes"),
        ("api.v1.routes.auth", "API auth routes"),
        ("api.v1.schemas.common", "API common schemas"),
        
        # Test LLM imports
        ("llm", "LLM module"),
        ("llm.handlers.openai", "OpenAI handler"),
        ("llm.handlers.anthropic", "Anthropic handler"),
        ("llm.storage.conversations", "Conversation storage"),
        
        # Test utils imports
        ("utils", "Utils module"),
        ("utils.monitoring.metrics", "Monitoring metrics"),
        ("utils.file_processing.processor", "File processor"),
        ("utils.config.loader", "Config loader"),
        
        # Test integrations
        ("integrations.google_auth", "Google auth integration"),
        ("integrations.google_calendar_service", "Google calendar service"),
    ]
    
    for module_path, description in tests:
        total_tests += 1
        if test_import(module_path, description):
            success_count += 1
    
    print(f"\nValidation Results: {success_count}/{total_tests} imports successful")
    
    if success_count == total_tests:
        print("🎉 All imports successful! Migration completed successfully.")
        return 0
    else:
        print("❌ Some imports failed. Review and fix before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
