# flaskllm/core/error_handler.py
"""
Error handler module for Flask LLM API.

This module provides centralized error handling functionality for the application,
including consistent error response formatting and integration with the error_codes module.
"""

import traceback
from typing import Dict, Any, Optional, Tuple, Type, Union

from flask import jsonify, Response, current_app
from pydantic import ValidationError

from core.error_codes import ErrorCode, get_error_details
from core.exceptions import APIError, AuthenticationError, ValidationError as AppValidationError
from core.logging import get_logger

logger = get_logger(__name__)


def format_error_response(
    error_code: ErrorCode,
    message: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    exception: Optional[Exception] = None,
) -> Tuple[Dict[str, Any], int]:
    """
    Format an error response for API endpoints.
    
    Args:
        error_code: The error code enum value
        message: Optional custom error message (overrides default for the error code)
        details: Optional additional error details for debugging
        exception: Optional exception that caused the error
        
    Returns:
        Tuple of (response_body, status_code)
    """
    error_info = get_error_details(error_code, message)
    status_code = error_info.pop("status_code")
    
    response = {
        "error": error_info["message"],
        "code": error_info["code"],
    }
    
    # Include additional details in development mode
    if details:
        response["details"] = details
        
    if current_app.debug and exception:
        response["exception"] = str(exception)
        response["traceback"] = traceback.format_exc()
    
    return response, status_code


def handle_api_error(error: APIError) -> Response:
    """
    Handle APIError exceptions.
    
    Args:
        error: The APIError instance
        
    Returns:
        Flask Response object
    """
    logger.error(
        "api_error", 
        error_type=error.__class__.__name__,
        message=str(error),
        status_code=error.status_code
    )
    
    # Map custom error to error code if possible
    error_code = getattr(error, "error_code", ErrorCode.INTERNAL_SERVER_ERROR)
    
    response, status_code = format_error_response(
        error_code=error_code,
        message=str(error),
        exception=error
    )
    
    return jsonify(response), status_code


def handle_validation_error(error: Union[ValidationError, AppValidationError]) -> Response:
    """
    Handle validation errors (both Pydantic and application validation).
    
    Args:
        error: The validation error
        
    Returns:
        Flask Response object
    """
    logger.warning("validation_error", error=str(error))
    
    details = None
    if hasattr(error, "errors"):  # Pydantic ValidationError
        details = {"validation_errors": error.errors()}
    
    response, status_code = format_error_response(
        error_code=ErrorCode.INVALID_REQUEST_FORMAT,
        message=str(error),
        details=details,
        exception=error
    )
    
    return jsonify(response), status_code


def handle_auth_error(error: AuthenticationError) -> Response:
    """
    Handle authentication errors.
    
    Args:
        error: The authentication error
        
    Returns:
        Flask Response object
    """
    logger.warning(
        "auth_error", 
        error_type=error.__class__.__name__,
        message=str(error)
    )
    
    # Map to specific error code based on the authentication error type
    if "missing" in str(error).lower():
        error_code = ErrorCode.MISSING_TOKEN
    elif "invalid" in str(error).lower():
        error_code = ErrorCode.INVALID_TOKEN
    elif "expired" in str(error).lower():
        error_code = ErrorCode.EXPIRED_TOKEN
    else:
        error_code = ErrorCode.INSUFFICIENT_PERMISSIONS
    
    response, status_code = format_error_response(
        error_code=error_code,
        message=str(error),
        exception=error
    )
    
    return jsonify(response), status_code


def handle_rate_limit_error(error: Exception) -> Response:
    """
    Handle rate limiting errors.
    
    Args:
        error: The rate limit error
        
    Returns:
        Flask Response object
    """
    logger.warning("rate_limit_error", message=str(error))
    
    response, status_code = format_error_response(
        error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
        message=str(error),
        exception=error
    )
    
    return jsonify(response), status_code


def handle_generic_error(error: Exception) -> Response:
    """
    Handle any unhandled exceptions.
    
    Args:
        error: The unhandled exception
        
    Returns:
        Flask Response object
    """
    logger.error(
        "unhandled_error",
        error_type=error.__class__.__name__,
        message=str(error),
        traceback=traceback.format_exc()
    )
    
    response, status_code = format_error_response(
        error_code=ErrorCode.INTERNAL_SERVER_ERROR,
        message="An unexpected error occurred",
        exception=error
    )
    
    return jsonify(response), status_code


def register_error_handlers(app) -> None:
    """
    Register error handlers with a Flask application.
    
    Args:
        app: The Flask application instance
    """
    # Custom exceptions
    app.register_error_handler(APIError, handle_api_error)
    app.register_error_handler(AuthenticationError, handle_auth_error)
    app.register_error_handler(AppValidationError, handle_validation_error)
    
    # Pydantic validation errors
    app.register_error_handler(ValidationError, handle_validation_error)
    
    # Generic error handler as fallback
    app.register_error_handler(Exception, handle_generic_error)
    
    # Additional error handlers can be registered here
