# flaskllm/core/exceptions.py
"""
Custom exceptions for the application.

This module defines all custom exceptions used throughout the application to provide
consistent error handling and meaningful error messages to clients.
"""
from typing import Any, Dict, Optional

from flask import current_app, jsonify, request

# Import error codes dynamically to avoid circular imports
# The ErrorCode enum will be imported when needed


class APIError(Exception):
    """Base class for API errors."""

    status_code = 500
    message = "An unknown error occurred"
    
    @property
    def error_code(self):
        # Import ErrorCode dynamically to avoid circular imports
        from core.error_codes import ErrorCode
        return ErrorCode.INTERNAL_SERVER_ERROR

    def __init__(
        self, message: Optional[str] = None, status_code: Optional[int] = None, 
        error_code: Optional[str] = None
    ):
        """
        Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code
            error_code: Error code from error_codes.py
        """
        if message:
            self.message = message
        if status_code:
            self.status_code = status_code
        if error_code:
            self.error_code = error_code
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert error to dictionary for JSON response.

        Returns:
            Dictionary representation of error
        """
        return {
            "error": self.message,
            "code": self.error_code
        }


# ---- Authentication and Authorization Errors -----

class AuthenticationError(APIError):
    """Error for authentication failures."""

    status_code = 401
    message = "Authentication failed"
    
    @property
    def error_code(self):
        # Import ErrorCode dynamically to avoid circular imports
        from core.error_codes import ErrorCode
        return ErrorCode.INVALID_TOKEN


# ---- Validation Errors -----

class ValidationError(APIError):
    """Error for validation failures."""

    status_code = 400
    message = "Validation failed"
    
    @property
    def error_code(self):
        # Import ErrorCode dynamically to avoid circular imports
        from core.error_codes import ErrorCode
        return ErrorCode.INVALID_REQUEST_FORMAT


class InvalidInputError(APIError):
    """Error for invalid input data."""

    status_code = 400
    message = "Invalid input data"
    
    @property
    def error_code(self):
        from core.error_codes import ErrorCode
        return ErrorCode.INVALID_FIELD_VALUE


# ---- Rate Limiting Errors -----

class RateLimitExceeded(APIError):
    """Error for rate limit exceeded."""

    status_code = 429
    message = "Rate limit exceeded"
    
    @property
    def error_code(self):
        from core.error_codes import ErrorCode
        return ErrorCode.RATE_LIMIT_EXCEEDED


# Alias for backward compatibility with tests
RateLimitExceededError = RateLimitExceeded


# ---- External Service Errors -----

class LLMAPIError(APIError):
    """Error for LLM API failures."""

    status_code = 502
    message = "LLM API error"
    
    @property
    def error_code(self):
        from core.error_codes import ErrorCode
        return ErrorCode.LLM_API_ERROR


# DEPRECATED: Use the functionality in error_handler.py instead
def setup_error_handlers(app: Any) -> None:
    """
    Register error handlers for the application.
    
    DEPRECATED: This function is deprecated and will be removed in a future version.
    Use register_error_handlers() from core.error_handler instead.

    Args:
        app: Flask application
    """

    @app.errorhandler(APIError)
    def handle_api_error(error: APIError) -> tuple[Dict[str, Any], int]:
        """Handle API errors."""
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(404)
    def handle_not_found(error: Any) -> tuple[Dict[str, Any], int]:
        """Handle 404 errors."""
        current_app.logger.info(f"Route not found: {request.path}")
        from core.error_codes import ErrorCode
        return jsonify({"error": "Resource not found", "code": ErrorCode.RESOURCE_NOT_FOUND}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error: Any) -> tuple[Dict[str, Any], int]:
        """Handle 405 errors."""
        current_app.logger.info(f"Method not allowed: {request.method} {request.path}")
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def handle_server_error(error: Any) -> tuple[Dict[str, Any], int]:
        """Handle 500 errors."""
        current_app.logger.exception("Unexpected server error")
        from core.error_codes import ErrorCode
        return jsonify({"error": "Internal server error", "code": ErrorCode.INTERNAL_SERVER_ERROR}), 500

# ---- Infrastructure Errors -----

class CacheError(APIError):
    """Cache layer failure."""

    status_code = 500
    message = "Cache error"
    
    @property
    def error_code(self):
        from core.error_codes import ErrorCode
        return ErrorCode.CACHE_UNAVAILABLE


# ---- Feature-specific Errors -----

class TemplateError(APIError):
    """Error for template operations."""

    status_code = 400
    message = "Template operation failed"
    
    @property
    def error_code(self):
        from core.error_codes import ErrorCode
        return ErrorCode.INVALID_FIELD_VALUE


class ConversationError(APIError):
    """Error for conversation operations."""

    status_code = 400
    message = "Conversation operation failed"
    
    @property
    def error_code(self):
        from core.error_codes import ErrorCode
        return ErrorCode.INVALID_FIELD_VALUE


class FileProcessingError(APIError):
    """Error for file processing operations."""

    status_code = 400
    message = "File processing failed"
    
    @property
    def error_code(self):
        from core.error_codes import ErrorCode
        return ErrorCode.INVALID_FIELD_VALUE


class SettingsError(APIError):
    """Error for settings operations."""

    status_code = 400
    message = "Settings operation failed"
    
    @property
    def error_code(self):
        from core.error_codes import ErrorCode
        return ErrorCode.CONFIGURATION_ERROR


class CalendarError(APIError):
    """Error for calendar operations."""

    status_code = 400
    message = "Calendar operation failed"
    
    @property
    def error_code(self):
        from core.error_codes import ErrorCode
        return ErrorCode.INVALID_FIELD_VALUE
