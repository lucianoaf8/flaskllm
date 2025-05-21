# tests/integration/test_api.py
"""
Integration tests for the API.
"""
import json
from unittest.mock import patch

import pytest

from app import create_app
from core.config import EnvironmentType, Settings


@pytest.fixture
def app():
    """Create an application for testing."""
    # Create test settings
    test_settings = Settings(
        environment=EnvironmentType.TESTING,
        api_token="test_token",
        openai_api_key="test_openai_key",
        debug=True,
        rate_limit_enabled=False,
    )

    # Create app with test settings
    app = create_app(test_settings)
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    with app.test_client() as client:
        yield client


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "ok"
    assert "version" in data


def test_webhook_missing_token(client):
    """Test webhook without authentication token."""
    response = client.post("/api/v1/webhook", json={"prompt": "Test prompt"})
    assert response.status_code == 401
    data = json.loads(response.data)
    assert "error" in data


def test_webhook_invalid_json(client):
    """Test webhook with invalid JSON."""
    response = client.post(
        "/api/v1/webhook", data="not json", headers={"X-API-Token": "test_token"}
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


def test_webhook_missing_prompt(client):
    """Test webhook with missing prompt."""
    response = client.post(
        "/api/v1/webhook",
        json={"not_prompt": "value"},
        headers={"X-API-Token": "test_token"},
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


@patch("llm.openai_handler.OpenAIHandler.process_prompt")
def test_webhook_success(mock_process_prompt, client):
    """Test successful webhook call."""
    # Mock the LLM handler
    mock_process_prompt.return_value = "Test response"

    # Call the webhook
    response = client.post(
        "/api/v1/webhook",
        json={"prompt": "Test prompt"},
        headers={"X-API-Token": "test_token"},
    )

    # Verify response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["summary"] == "Test response"
    assert "processing_time" in data

    # Verify mock was called
    mock_process_prompt.assert_called_once_with(
        prompt="Test prompt", source="other", language="en", type="summary"
    )
