# core/exceptions.py
"""
Custom exceptions for the application.
"""
from typing import Dict, Any, Optional
from flask import jsonify, current_app, request


class APIError(Exception):
    """Base class for API errors."""

    status_code = 500
    message = "An unknown error occurred"

    def __init__(
        self, message: Optional[str] = None, status_code: Optional[int] = None
    ):
        """
        Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code
        """
        if message:
            self.message = message
        if status_code:
            self.status_code = status_code
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert error to dictionary for JSON response.

        Returns:
            Dictionary representation of error
        """
        return {"error": self.message}


class InvalidInputError(APIError):
    """Error for invalid input data."""

    status_code = 400
    message = "Invalid input data"


class AuthenticationError(APIError):
    """Error for authentication failures."""

    status_code = 401
    message = "Authentication failed"


class RateLimitExceeded(APIError):
    """Error for rate limit exceeded."""

    status_code = 429
    message = "Rate limit exceeded"


class LLMAPIError(APIError):
    """Error for LLM API failures."""

    status_code = 502
    message = "LLM API error"


def setup_error_handlers(app: Any) -> None:
    """
    Register error handlers for the application.

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
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error: Any) -> tuple[Dict[str, Any], int]:
        """Handle 405 errors."""
        current_app.logger.info(f"Method not allowed: {request.method} {request.path}")
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def handle_server_error(error: Any) -> tuple[Dict[str, Any], int]:
        """Handle 500 errors."""
        current_app.logger.exception("Unexpected server error")
        return jsonify({"error": "Internal server error"}), 500
