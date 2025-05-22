# utils/rate_limiter.py
"""
Rate Limiting Module

This module provides rate limiting functionality for the API endpoints.
"""
from typing import Any, Callable, Optional

from flask import Flask, Response, current_app, g, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from core.exceptions import RateLimitExceeded
from core.logging import get_logger

# Configure logger
logger = get_logger(__name__)

# Global limiter instance
limiter: Optional[Limiter] = None


def get_rate_limit_key() -> str:
    """
    Get the key for rate limiting, based on API token if available.

    Returns:
        String key for rate limiting
    """
    # Check if the request has been authenticated with an API token
    if hasattr(g, "api_token") and g.api_token:
        # Use the API token as the rate limit key
        return f"token:{g.api_token}"

    # Fall back to remote address
    return get_remote_address()


def configure_rate_limiting(app: Flask) -> None:
    """
    Configure rate limiting for the application.

    Args:
        app: Flask application instance
    """
    global limiter

    settings = app.config["SETTINGS"]

    # Skip if rate limiting is disabled
    if not settings.rate_limit_enabled:
        logger.info("Rate limiting is disabled")
        return

    # Create limiter instance
    limiter = Limiter(
        app=app,
        key_func=get_rate_limit_key,
        default_limits=[f"{settings.rate_limit} per minute"],
        storage_uri="memory://",  # Use memory storage for simplicity
        strategy="fixed-window",  # Use fixed window strategy
    )

    # Register custom error handler for rate limit exceeded
    @limiter.request_filter
    def check_if_testing() -> bool:
        """
        Skip rate limiting in testing environment.

        Returns:
            True if testing environment, False otherwise
        """
        return settings.environment == "testing"

    @app.errorhandler(429)
    def handle_rate_limit_exceeded(e: Any) -> Response:
        """
        Handle rate limit exceeded errors.

        Args:
            e: Exception instance

        Returns:
            JSON response with error details
        """
        logger.warning(
            "Rate limit exceeded",
            path=request.path,
            method=request.method,
            remote_addr=request.remote_addr,
        )

        error = RateLimitExceeded(
            message="Rate limit exceeded",
        )

        response = jsonify(error.to_dict())
        response.status_code = error.status_code

        # Add rate limit headers
        response.headers.extend(
            {
                "X-RateLimit-Limit": str(settings.rate_limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": "60",  # Reset after 60 seconds
            }
        )

        return response

    logger.info("Rate limiting configured", rate_limit=settings.rate_limit)


def apply_rate_limit(
    limit_value: str, key_func: Optional[Callable[[], str]] = None
) -> Callable:
    """
    Decorator for applying rate limits to specific routes.

    Args:
        limit_value: Rate limit string (e.g., "10 per minute")
        key_func: Function to get the rate limit key

    Returns:
        Decorator function
    """
    global limiter

    def decorator(f: Callable) -> Callable:
        if limiter and current_app.config["SETTINGS"].rate_limit_enabled:
            return limiter.limit(limit_value, key_func=key_func or get_rate_limit_key)(
                f
            )
        return f

    return decorator


# Alias for RateLimitExceeded to maintain backward compatibility
RateLimitExceededError = RateLimitExceeded


# Simple in-memory rate limiter for tests and fallback
class RateLimiter:
    """
    Simple in-memory rate limiter implementation.
    
    This class provides basic rate limiting functionality with a fixed window strategy.
    It's used primarily for testing and as a fallback when Flask-Limiter is not configured.
    """
    
    def __init__(self, limit: int = 60, window: int = 60):
        """
        Initialize the rate limiter.
        
        Args:
            limit: Maximum number of requests per window
            window: Time window in seconds
        """
        self.limit = limit
        self.window = window
        self.tokens = {}  # Dict to store tokens and their request counts
    
    def get_remaining(self, token: str) -> int:
        """
        Get remaining requests for a token.
        
        Args:
            token: Rate limiting token/key
            
        Returns:
            Number of remaining requests
        """
        if token not in self.tokens:
            return self.limit
            
        count = self.tokens.get(token, 0)
        return max(0, self.limit - count)
    
    def check_rate_limit(self, token: str) -> bool:
        """
        Check if a token has exceeded its rate limit.
        
        Args:
            token: Rate limiting token/key
            
        Returns:
            True if rate limit is not exceeded, False otherwise
        """
        if token not in self.tokens:
            self.tokens[token] = 1
            return True
            
        count = self.tokens.get(token, 0)
        if count >= self.limit:
            return False
            
        self.tokens[token] = count + 1
        return True
    
    def reset(self, token: Optional[str] = None) -> None:
        """
        Reset rate limit counters.
        
        Args:
            token: Token to reset (None to reset all)
        """
        if token is None:
            self.tokens = {}
        elif token in self.tokens:
            self.tokens[token] = 0

    def is_rate_limited(self) -> bool:
        """Check if the current request is rate limited."""
        key = self._get_key()
        self._clean_old_requests()
        
        if key not in self.requests:
            return False
            
        return len(self.requests[key]) >= self.limit
        
    def _get_key(self) -> str:
        """Get the key for rate limiting."""
        try:
            from flask import request
            return f"rate_limit:{request.remote_addr}"
        except:
            return "rate_limit:unknown"
            
    def _clean_old_requests(self):
        """Remove old requests outside the time window."""
        import time
        current_time = time.time()
        
        for key in list(self.requests.keys()):
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if current_time - req_time < self.window
            ]
            
            if not self.requests[key]:
                del self.requests[key]


# Decorator for simple rate limiting without Flask-Limiter
def rate_limit(limit: int = 60, window: int = 60, key_func: Optional[Callable[[], str]] = None):
    """
    Decorator for rate limiting specific routes without Flask-Limiter.
    
    Args:
        limit: Maximum number of requests per window
        window: Time window in seconds
        key_func: Function to get the rate limit key
        
    Returns:
        Decorator function
    """
    limiter = RateLimiter(limit=limit, window=window)
    
    def decorator(f: Callable) -> Callable:
        def wrapped(*args, **kwargs):
            # Get token for rate limiting
            token = key_func() if key_func else get_rate_limit_key()
            
            # Check rate limit
            if not limiter.check_rate_limit(token):
                raise RateLimitExceededError(
                    message=f"Rate limit of {limit} requests per {window} seconds exceeded"
                )
                
            return f(*args, **kwargs)
        
        # Preserve function attributes
        wrapped.__name__ = f.__name__
        wrapped.__doc__ = f.__doc__
        
        return wrapped
    
    return decorator
