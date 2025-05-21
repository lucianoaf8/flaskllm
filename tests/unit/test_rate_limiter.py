# tests/unit/test_rate_limiter.py
"""
Tests for rate limiting functionality.
"""
import pytest
import time
from unittest.mock import patch, MagicMock

from flask import Flask, request, Response
from flask.testing import FlaskClient

from utils.rate_limiter import RateLimiter, rate_limit, RateLimitExceededError


class TestRateLimiter:
    """Test suite for RateLimiter class."""

    @pytest.fixture
    def limiter(self):
        """Create a RateLimiter instance for testing."""
        return RateLimiter(
            limit=5,  # 5 requests
            window=60  # per minute
        )
    
    def test_rate_limiter_init(self, limiter):
        """Test RateLimiter initialization."""
        assert limiter.limit == 5
        assert limiter.window == 60
        assert isinstance(limiter.requests, dict)
    
    def test_rate_limiter_get_key(self, limiter):
        """Test generating request keys."""
        # Mock request with remote addr
        with patch.object(request, "remote_addr", "127.0.0.1"):
            key = limiter._get_key()
            assert "127.0.0.1" in key
        
        # Mock request with different IP
        with patch.object(request, "remote_addr", "192.168.1.1"):
            key = limiter._get_key()
            assert "192.168.1.1" in key
    
    def test_rate_limiter_clean_old_requests(self, limiter):
        """Test cleaning old requests."""
        # Add some requests
        now = time.time()
        
        # Add recent requests (should be kept)
        limiter.requests["key1"] = [now - 10]
        
        # Add old requests (should be removed)
        limiter.requests["key2"] = [now - 70]  # Older than window (60s)
        
        # Clean old requests
        limiter._clean_old_requests()
        
        # Check results
        assert "key1" in limiter.requests
        assert "key2" not in limiter.requests
    
    def test_rate_limiter_is_rate_limited(self, limiter):
        """Test rate limiting logic."""
        # Mock request key
        with patch.object(limiter, "_get_key", return_value="test_key"):
            # No requests yet, should not be limited
            assert not limiter.is_rate_limited()
            
            # Add 4 requests (below limit)
            now = time.time()
            limiter.requests["test_key"] = [now - 10] * 4
            assert not limiter.is_rate_limited()
            
            # Add 1 more request (at limit)
            limiter.requests["test_key"].append(now)
            assert not limiter.is_rate_limited()
            
            # Add 1 more request (exceeds limit)
            limiter.requests["test_key"].append(now)
            assert limiter.is_rate_limited()
    
    def test_rate_limiter_add_request(self, limiter):
        """Test adding requests."""
        # Mock request key and time
        with patch.object(limiter, "_get_key", return_value="test_key"):
            with patch("time.time", return_value=1000):
                # Add first request
                limiter.add_request()
                assert "test_key" in limiter.requests
                assert limiter.requests["test_key"] == [1000]
                
                # Add another request
                limiter.add_request()
                assert limiter.requests["test_key"] == [1000, 1000]
    
    def test_rate_limit_decorator(self):
        """Test rate_limit decorator."""
        # Create a test app
        app = Flask(__name__)
        
        # Create a rate-limited endpoint
        @app.route("/test")
        @rate_limit(limit=2, window=60)
        def test_endpoint():
            return "OK"
        
        # Create a test client
        client = app.test_client()
        
        # Mock the RateLimiter instance
        with patch("utils.rate_limiter.RateLimiter") as MockLimiter:
            # Configure the mock
            limiter_instance = MockLimiter.return_value
            
            # First request - not limited
            limiter_instance.is_rate_limited.return_value = False
            response = client.get("/test")
            assert response.status_code == 200
            assert response.data == b"OK"
            limiter_instance.add_request.assert_called_once()
            
            # Reset the mock
            limiter_instance.add_request.reset_mock()
            
            # Second request - rate limited
            limiter_instance.is_rate_limited.return_value = True
            response = client.get("/test")
            assert response.status_code == 429
            assert b"Rate limit exceeded" in response.data
            limiter_instance.add_request.assert_not_called()

    def test_rate_limiter_headers(self):
        """Test rate limit headers in response."""
        # Create a test app
        app = Flask(__name__)
        
        # Create a rate-limited endpoint
        @app.route("/test-headers")
        @rate_limit(limit=10, window=60)
        def test_headers():
            return "OK"
        
        # Create a test client
        client = app.test_client()
        
        # Mock the RateLimiter
        with patch("utils.rate_limiter.RateLimiter") as MockLimiter:
            # Configure the mock
            limiter_instance = MockLimiter.return_value
            limiter_instance.is_rate_limited.return_value = False
            
            # Mock the number of requests
            limiter_instance.requests = {"test_key": [time.time()] * 3}
            with patch.object(limiter_instance, "_get_key", return_value="test_key"):
                # Send request
                response = client.get("/test-headers")
                
                # Check headers
                assert "X-RateLimit-Limit" in response.headers
                assert response.headers["X-RateLimit-Limit"] == "10"
                
                assert "X-RateLimit-Remaining" in response.headers
                assert response.headers["X-RateLimit-Remaining"] == "7"
                
                assert "X-RateLimit-Reset" in response.headers
                # Reset time is dynamic, so just check it exists
                assert response.headers["X-RateLimit-Reset"]