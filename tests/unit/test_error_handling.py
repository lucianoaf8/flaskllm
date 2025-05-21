# tests/unit/test_error_handling.py
"""
Tests for error handling functionality.
"""
import json
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from core.exceptions import (
    APIError,
    AuthenticationError,
    InvalidInputError,
    LLMAPIError,
    RateLimitExceededError,
    setup_error_handlers,
)


class TestErrorHandling:
    """Test suite for error handling."""

    @pytest.fixture
    def app(self):
        """Create a test Flask app with error handlers."""
        app = Flask(__name__)
        setup_error_handlers(app)

        # Add test routes that raise different errors
        @app.route("/test-api-error")
        def test_api_error():
            raise APIError("Test API error")

        @app.route("/test-auth-error")
        def test_auth_error():
            raise AuthenticationError("Test auth error")

        @app.route("/test-input-error")
        def test_input_error():
            raise InvalidInputError("Test input error")

        @app.route("/test-llm-error")
        def test_llm_error():
            raise LLMAPIError("Test LLM API error")

        @app.route("/test-rate-limit-error")
        def test_rate_limit_error():
            raise RateLimitExceededError("Test rate limit error")

        @app.route("/test-http-exception")
        def test_http_exception():
            raise HTTPException(description="Test HTTP exception")

        @app.route("/test-generic-exception")
        def test_generic_exception():
            raise Exception("Test generic exception")

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    def test_api_error_handler(self, client):
        """Test handling of APIError."""
        response = client.get("/test-api-error")
        assert response.status_code == 500
        data = json.loads(response.data)
        assert "error" in data
        assert "Test API error" in data["error"]

    def test_authentication_error_handler(self, client):
        """Test handling of AuthenticationError."""
        response = client.get("/test-auth-error")
        assert response.status_code == 401
        data = json.loads(response.data)
        assert "error" in data
        assert "Test auth error" in data["error"]

    def test_invalid_input_error_handler(self, client):
        """Test handling of InvalidInputError."""
        response = client.get("/test-input-error")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "Test input error" in data["error"]

    def test_llm_api_error_handler(self, client):
        """Test handling of LLMAPIError."""
        response = client.get("/test-llm-error")
        assert response.status_code == 502
        data = json.loads(response.data)
        assert "error" in data
        assert "Test LLM API error" in data["error"]

    def test_rate_limit_exceeded_error_handler(self, client):
        """Test handling of RateLimitExceededError."""
        response = client.get("/test-rate-limit-error")
        assert response.status_code == 429
        data = json.loads(response.data)
        assert "error" in data
        assert "Test rate limit error" in data["error"]

    def test_http_exception_handler(self, client):
        """Test handling of HTTPException."""
        response = client.get("/test-http-exception")
        assert response.status_code == 500  # Default status code
        data = json.loads(response.data)
        assert "error" in data
        assert "Test HTTP exception" in data["error"]

    def test_generic_exception_handler(self, client):
        """Test handling of generic Exception."""
        # In production, this would log the error
        with patch("flask.current_app.logger.exception") as mock_logger:
            response = client.get("/test-generic-exception")
            assert response.status_code == 500
            data = json.loads(response.data)
            assert "error" in data
            assert "Internal server error" in data["error"]

            # Verify the exception was logged
            mock_logger.assert_called_once()

    def test_error_response_format(self, client):
        """Test format of error responses."""
        response = client.get("/test-input-error")
        data = json.loads(response.data)

        # Check expected fields
        assert "error" in data
        assert isinstance(data["error"], str)

        # Other fields that might be present depending on implementation
        if "details" in data:
            assert isinstance(data["details"], str)
        if "code" in data:
            assert isinstance(data["code"], str)
