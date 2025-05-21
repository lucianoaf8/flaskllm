# flaskllm/tests/conftest.py
"""
Test Fixtures Module

This module provides pytest fixtures for testing.
"""
from typing import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app
from core.config import EnvironmentType, Settings


@pytest.fixture
def app() -> Generator[Flask, None, None]:
    """
    Create and configure a Flask application for testing.

    Yields:
        Flask application configured for testing
    """
    # Create test settings
    test_settings = Settings(
        environment=EnvironmentType.TESTING,
        debug=True,
        api_token="test_token",
        llm_provider="openai",
        openai_api_key="test_openai_key",
        rate_limit_enabled=False,  # Disable rate limiting for tests
    )

    # Create app with test settings
    app = create_app(test_settings)

    # Set testing flag
    app.testing = True

    yield app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """
    Create a test client for the application.

    Args:
        app: Flask application

    Returns:
        Flask test client
    """
    return app.test_client()


@pytest.fixture
def auth_headers() -> dict:
    """
    Create headers with authentication token for testing.

    Returns:
        Dictionary of headers including authentication token
    """
    return {"X-API-Token": "test_token", "Content-Type": "application/json"}
