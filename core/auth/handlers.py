# core/auth/handlers.py
"""
Authentication Module

This module provides authentication mechanisms for the API,
including API token validation and decorator for protected routes.
"""
import functools
import hmac
import os
from typing import Any, Callable, List, Optional, TypeVar, Union, cast

from flask import current_app, g, request

from ..exceptions import AuthenticationError
from ..logging import get_logger
from .tokens import TokenScope, TokenService

# Configure logger
logger = get_logger(__name__)

# Define callable type for the decorator
F = TypeVar("F", bound=Callable[..., Any])


def validate_token(token: str) -> bool:
    """
    Validate an API token.
    
    This function validates tokens against both the legacy single token system
    and the new token management system.
    
    Args:
        token: Token to validate
        
    Returns:
        True if the token is valid, False otherwise
    """
    # First try the new token system
    token_service = current_app.config.get("TOKEN_SERVICE")
    if token_service:
        validated_token = token_service.validate_token(token)
        if validated_token:
            # Store the token in g for later use
            g.token = validated_token
            g.token_scope = validated_token.scope
            return True
    
    # Fall back to legacy token validation
    settings = current_app.config["SETTINGS"]
    legacy_token = settings.api_token
    
    # Use constant time comparison to prevent timing attacks
    is_legacy_valid = hmac.compare_digest(token, legacy_token)
    
    if is_legacy_valid:
        # No token object for legacy tokens, but set basic scope
        g.token_scope = [TokenScope.READ, TokenScope.WRITE]
        return True
    
    return False


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


def auth_required(
    f: Optional[F] = None,
    required_scope: Optional[Union[TokenScope, List[TokenScope]]] = None
) -> Any:
    """
    Decorator for routes that require authentication.
    
    This decorator validates the API token and checks for required scopes.

    Args:
        f: Route function to decorate
        required_scope: Required scope(s) for the route
        
    Returns:
        Decorated function that validates authentication before proceeding

    Raises:
        AuthenticationError: If authentication fails or required scopes are missing
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
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

            # Validate the token
            if not validate_token(token):
                logger.warning(
                    "Authentication failed: Invalid token",
                    path=request.path,
                    method=request.method,
                    remote_addr=request.remote_addr,
                )
                raise AuthenticationError("Invalid API token")

            # Check for required scopes
            if required_scope:
                required_scopes = [required_scope] if isinstance(required_scope, TokenScope) else required_scope
                token_scope = getattr(g, "token_scope", [])
                
                for scope in required_scopes:
                    if scope not in token_scope:
                        logger.warning(
                            f"Authorization failed: Missing required scope: {scope}",
                            path=request.path,
                            method=request.method,
                            remote_addr=request.remote_addr,
                        )
                        raise AuthenticationError(f"Token missing required scope: {scope}")

            # Store authentication info in g for potential later use
            g.authenticated = True

            # Log successful authentication
            logger.debug(
                "Authentication successful", 
                path=request.path, 
                method=request.method
            )

            # Call the original function
            return func(*args, **kwargs)

        return cast(F, decorated_function)
    
    # Handle case where decorator is used without arguments
    if f is not None:
        return decorator(f)
    
    return decorator


def admin_required(f: F) -> F:
    """
    Decorator for routes that require admin scope.
    
    Args:
        f: Route function to decorate
        
    Returns:
        Decorated function that validates admin scope before proceeding
    """
    return auth_required(required_scope=TokenScope.ADMIN)(f)
