# flaskllm/tests/unit/test_auth.py
"""
Tests for authentication module.
"""
from unittest.mock import MagicMock, patch, Mock

import pytest
from flask import Flask

from core.auth import auth_required, get_token_from_request, validate_token
from core.exceptions import AuthenticationError


class TestAuth:
    """Test authentication functions."""
    
    def test_get_token_from_request(self):
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

    def test_auth_required_decorator(self):
        """Test auth_required decorator."""
        app = Flask(__name__)
        
        # Create a mock settings object
        mock_settings = MagicMock()
        mock_settings.api_token = "test_token"
        
        # Set up the app config
        app.config["SETTINGS"] = mock_settings
        app.config["TOKEN_SERVICE"] = None  # No token service for basic test
        
        # Create a test route
        @auth_required
        def test_route():
            return "Success"
        
        # Test with valid token
        with app.test_request_context(headers={"X-API-Token": "test_token"}):
            with app.app_context():
                result = test_route()
                assert result == "Success"
        
        # Test with invalid token
        with app.test_request_context(headers={"X-API-Token": "wrong_token"}):
            with app.app_context():
                with pytest.raises(AuthenticationError):
                    test_route()
        
        # Test with no token
        with app.test_request_context():
            with app.app_context():
                with pytest.raises(AuthenticationError):
                    test_route()

    def test_validate_token_with_expected(self):
        """Test validate_token with expected token parameter."""
        app = Flask(__name__)
        
        # Create a mock settings object
        mock_settings = MagicMock()
        mock_settings.api_token = "test_token"
        
        # Set up the app config
        app.config["SETTINGS"] = mock_settings
        app.config["TOKEN_SERVICE"] = None
        
        with app.app_context():
            # Test with matching tokens
            assert validate_token("test_token", "test_token") is True
            
            # Test with non-matching tokens
            assert validate_token("wrong_token", "test_token") is False
