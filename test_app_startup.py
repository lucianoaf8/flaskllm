#!/usr/bin/env python3
"""
test_app_startup.py - Simple test to verify the app can start
"""

import sys
import os

# Set up environment
os.environ.update({
    "ENVIRONMENT": "testing",
    "API_TOKEN": "test_token",
    "OPENAI_API_KEY": "test_key",
    "LLM_PROVIDER": "openai",
    "RATE_LIMIT_ENABLED": "False",
    "DEBUG": "True"
})

def test_imports():
    """Test if all modules can be imported."""
    print("🔍 Testing imports...")
    
    modules_to_test = [
        "core.config",
        "core.logging", 
        "core.exceptions",
        "core.auth",
        "api",
        "llm.factory",
        "app"
    ]
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module}")
        except Exception as e:
            print(f"❌ {module}: {e}")
            return False
            
    return True

def test_app_creation():
    """Test if the Flask app can be created."""
    print("\n🏗️ Testing app creation...")
    
    try:
        from app import create_app
        app = create_app()
        print("✅ App created successfully!")
        
        # Test if routes are registered
        print("\n📍 Registered routes:")
        for rule in app.url_map.iter_rules():
            if str(rule).startswith('/api/'):
                print(f"   {rule}")
                
        return True
        
    except Exception as e:
        print(f"❌ Failed to create app: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run startup tests."""
    print("🚀 Testing FlaskLLM App Startup")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed!")
        return 1
        
    # Test app creation
    if not test_app_creation():
        print("\n❌ App creation failed!")
        return 1
        
    print("\n✅ All startup tests passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())