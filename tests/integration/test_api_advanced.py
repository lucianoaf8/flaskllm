# tests/integration/test_api_advanced.py
"""
Advanced integration tests for the API.
"""
import json
import pytest
from unittest.mock import patch, MagicMock

from core.exceptions import LLMAPIError, RateLimitExceededError


@pytest.fixture
def auth_headers():
    """Authentication headers for API requests."""
    return {"X-API-Token": "test_token", "Content-Type": "application/json"}


@patch("llm.openai_handler.OpenAIHandler.process_prompt")
def test_webhook_with_all_parameters(mock_process_prompt, client, auth_headers):
    """Test webhook with all parameters."""
    # Setup mock
    mock_process_prompt.return_value = "Advanced test response"

    # Send request with all parameters
    data = {
        "prompt": "Process this text",
        "source": "email",
        "language": "es",
        "type": "translation"
    }
    response = client.post(
        "/api/v1/webhook",
        json=data,
        headers=auth_headers
    )

    # Verify response
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["summary"] == "Advanced test response"
    assert "processing_time" in result

    # Verify mock was called with correct parameters
    mock_process_prompt.assert_called_once_with(
        prompt="Process this text",
        source="email",
        language="es",
        type="translation"
    )


@patch("llm.factory.get_llm_handler")
def test_webhook_llm_api_error(mock_get_llm_handler, client, auth_headers):
    """Test webhook with LLM API error."""
    # Setup mock to raise an LLM API error
    mock_handler = MagicMock()
    mock_handler.process_prompt.side_effect = LLMAPIError("API error")
    mock_get_llm_handler.return_value = mock_handler

    # Send request
    response = client.post(
        "/api/v1/webhook",
        json={"prompt": "Test prompt"},
        headers=auth_headers
    )

    # Verify error response
    assert response.status_code == 502
    data = json.loads(response.data)
    assert "error" in data
    assert "API error" in data["error"]


@patch("llm.factory.get_llm_handler")
def test_webhook_rate_limit_exceeded(mock_get_llm_handler, client, auth_headers):
    """Test webhook with rate limit exceeded error."""
    # Setup mock to raise a rate limit error
    mock_handler = MagicMock()
    mock_handler.process_prompt.side_effect = RateLimitExceededError("Rate limit exceeded")
    mock_get_llm_handler.return_value = mock_handler

    # Send request
    response = client.post(
        "/api/v1/webhook",
        json={"prompt": "Test prompt"},
        headers=auth_headers
    )

    # Verify error response
    assert response.status_code == 429
    data = json.loads(response.data)
    assert "error" in data
    assert "Rate limit exceeded" in data["error"]


def test_webhook_invalid_content_type(client, auth_headers):
    """Test webhook with invalid content type."""
    # Remove content type header
    headers = {"X-API-Token": auth_headers["X-API-Token"]}
    
    # Send request with text instead of JSON
    response = client.post(
        "/api/v1/webhook",
        data="This is not JSON",
        headers=headers
    )

    # Verify error response
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


def test_cors_headers(client):
    """Test CORS headers in response."""
    # Send OPTIONS request to test CORS preflight
    response = client.options("/api/v1/health")
    
    # Verify CORS headers
    assert "Access-Control-Allow-Origin" in response.headers
    assert "Access-Control-Allow-Headers" in response.headers
    assert "Access-Control-Allow-Methods" in response.headers


def test_rate_limiting():
    """
    Test rate limiting functionality.
    
    Note: This test is commented out because rate limiting is disabled in test mode.
    In a real implementation, you would need to enable rate limiting for this test
    and then make multiple requests to trigger the rate limit.
    """
    # Skipping this test as it requires modifying the app config
    # which is not easily done in the current test setup
    pass