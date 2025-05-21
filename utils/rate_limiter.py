# flaskllm/utils/rate_limiter.py
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

        error = RateLimitExceeded(message="Rate limit exceeded", )

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
