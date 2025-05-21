# flaskllm/tests/unit/test_auth.py
"""
Tests for authentication module.
"""
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask, request

from core.auth import auth_required, get_token_from_request, validate_token
from core.exceptions import AuthenticationError


def test_validate_token():
    """Test token validation."""
    # Valid token
    assert validate_token("test_token", "test_token") is True

    # Invalid token
    assert validate_token("test_token", "wrong_token") is False


def test_get_token_from_request():
    """Test getting token from request."""
    # Create a Flask app for testing
    app = Flask(__name__)
    
    # Test with token in header
    with app.test_request_context(headers={"X-API-Token": "header_token"}):
        assert get_token_from_request() == "header_token"
    
    # Test with token in query parameter
    with app.test_request_context("/?api_token=query_token"):
        assert get_token_from_request() == "query_token"
    
    # Test with no token
    with app.test_request_context():
        assert get_token_from_request() is None


def test_auth_required_decorator():
    """Test auth_required decorator."""

    # Mock function to decorate
    @auth_required
    def test_route():
        return "Success"

    # Mock Flask app context
    app = Flask(__name__)
    app.config["SETTINGS"] = MagicMock(api_token="test_token")

    with app.test_request_context():
        # Valid token
        with patch(
            "core.auth.get_token_from_request", return_value="test_token"
        ):
            assert test_route() == "Success"

        # Invalid token
        with patch(
            "core.auth.get_token_from_request", return_value="wrong_token"
        ):
            with pytest.raises(AuthenticationError):
                test_route()

        # No token
        with patch("core.auth.get_token_from_request", return_value=None):
            with pytest.raises(AuthenticationError):
                test_route()
