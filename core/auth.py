# flaskllm/core/auth.py
"""
Authentication Module

This module provides authentication mechanisms for the API,
including API token validation and decorator for protected routes.
"""
import functools
import hmac
from typing import Any, Callable, Optional, TypeVar, cast

from flask import current_app, g, request

from core.exceptions import AuthenticationError
from core.logging import get_logger

# Configure logger
logger = get_logger(__name__)

# Define callable type for the decorator
F = TypeVar("F", bound=Callable[..., Any])


def validate_token(token: str, expected_token: str) -> bool:
    """
    Validate an API token against the expected token using constant time comparison.

    Args:
        token: Token to validate
        expected_token: Expected token value

    Returns:
        True if tokens match, False otherwise
    """
    # Use constant time comparison to prevent timing attacks
    return hmac.compare_digest(token, expected_token)


def get_token_from_request() -> Optional[str]:
    """
    Extract API token from request headers or query parameters.

    Returns:
        API token if found, None otherwise
    """
    # Check for token in headers (preferred method)
    token = request.headers.get("X-API-Token")

    # If not in headers, check query parameters
    if not token:
        token = request.args.get("api_token")

    return token


def auth_required(f: F) -> F:
    """
    Decorator for routes that require authentication.

    Args:
        f: Route function to decorate

    Returns:
        Decorated function that validates authentication before proceeding

    Raises:
        AuthenticationError: If authentication fails
    """

    @functools.wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        # Get the API token from the request
        token = get_token_from_request()

        if not token:
            logger.warning(
                "Authentication failed: No token provided",
                path=request.path,
                method=request.method,
                remote_addr=request.remote_addr,
            )
            raise AuthenticationError("API token is required")

        # Get the expected token from app config
        settings = current_app.config["SETTINGS"]
        expected_token = settings.api_token

        # Validate the token
        if not validate_token(token, expected_token):
            logger.warning(
                "Authentication failed: Invalid token",
                path=request.path,
                method=request.method,
                remote_addr=request.remote_addr,
            )
            raise AuthenticationError("Invalid API token")

        # Store authentication info in g for potential later use
        g.authenticated = True

        # Log successful authentication
        logger.debug(
            "Authentication successful", path=request.path, method=request.method
        )

        # Call the original function
        return f(*args, **kwargs)

    return cast(F, decorated_function)
