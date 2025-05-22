# flaskllm/tests/conftest.py
"""
Test Fixtures Module

This module provides pytest fixtures for testing.
"""
import os
import tempfile
from typing import Generator
from pathlib import Path

import pytest
from flask import Flask
from flask.testing import FlaskClient

# Set test environment variables before importing app
os.environ["ENVIRONMENT"] = "testing"
os.environ["API_TOKEN"] = "test_token"
os.environ["OPENAI_API_KEY"] = "test_openai_key"
os.environ["ANTHROPIC_API_KEY"] = "test_anthropic_key"
os.environ["LLM_PROVIDER"] = "openai"
os.environ["RATE_LIMIT_ENABLED"] = "False"
os.environ["DEBUG"] = "True"

from app import create_app
from core.config import EnvironmentType, Settings


@pytest.fixture
def app() -> Generator[Flask, None, None]:
    """Create and configure a Flask application for testing."""
    # Create test settings
    test_settings = Settings(
        environment=EnvironmentType.TESTING,
        debug=True,
        api_token="test_token",
        llm_provider="openai",
        openai_api_key="test_openai_key",
        anthropic_api_key="test_anthropic_key",
        rate_limit_enabled=False,
    )

    # Create app with test settings
    app = create_app(test_settings)
    app.testing = True

    yield app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Create a test client for the application."""
    return app.test_client()


@pytest.fixture
def auth_headers() -> dict:
    """Create headers with authentication token for testing."""
    return {"X-API-Token": "test_token", "Content-Type": "application/json"}


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname
