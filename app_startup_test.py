#!/usr/bin/env python3
# app_startup_test.py

"""
Simple script to test if the application can initialize properly.
This doesn't start the server, just checks if the app can be created without errors.
"""
import sys

try:
    print("Attempting to import the application...")
    from app import create_app
    print("✓ Import successful")
    
    print("Attempting to create the application...")
    app = create_app()
    print("✓ Application creation successful")
    
    print("\n🎉 Application startup test PASSED")
    sys.exit(0)
except Exception as e:
    print(f"❌ Error during application startup: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
