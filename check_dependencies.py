#!/usr/bin/env python3
"""
check_dependencies.py - Verify all required dependencies are installed
"""

import importlib
import importlib.util


def check_dependencies():
    """Check if all required dependencies are installed."""
    print("📦 Checking dependencies...")

    # Mapping of pip package name → importable module name
    required_packages = {
        "flask": "flask",
        "pydantic": "pydantic",
        "pydantic-settings": "pydantic_settings",
        "python-dotenv": "dotenv",
        "structlog": "structlog",
        "openai": "openai",
        "anthropic": "anthropic",
        "requests": "requests",
        "tenacity": "tenacity",
        "pytest": "pytest",
        "flask-cors": "flask_cors",
        "flask-limiter": "flask_limiter",
        "PyJWT": "jwt",
        "cryptography": "cryptography",
        "google-api-python-client": "googleapiclient",
        "google-auth-oauthlib": "google_auth_oauthlib",
        "google-auth-httplib2": "google_auth_httplib2",
    }

    missing = []

    for pip_name, import_name in required_packages.items():
        if importlib.util.find_spec(import_name):
            print(f"✅ {pip_name}")
        else:
            print(f"❌ {pip_name} - MISSING")
            missing.append(pip_name)

    if missing:
        print(f"\n⚠️ Missing packages: {', '.join(missing)}")
        print("Install with:")
        print(f"pip install {' '.join(missing)}")
    else:
        print("\n✅ All dependencies installed!")

if __name__ == "__main__":
    check_dependencies()
