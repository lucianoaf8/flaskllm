# core/middleware.py
"""
Middleware for the application.
"""
from typing import Any
from flask import Flask, request, g, current_app
import time
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from utils.rate_limiter import configure_rate_limiting
from core.config import get_settings


def setup_middleware(app: Flask) -> None:
    """
    Set up middleware for the application.

    Args:
        app: Flask application
    """
    # Fix for proper IP behind proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    # Set up CORS
    _setup_cors(app)

    # Set up rate limiter
    _setup_rate_limiter(app)

    # Request logging and timing
    _setup_request_logging(app)

    # Security headers
    _setup_security_headers(app)


def _setup_cors(app: Flask) -> None:
    """
    Set up CORS for the application.

    Args:
        app: Flask application
    """
    settings = get_settings()
    CORS(
        app,
        resources={r"/api/*": {"origins": settings.allowed_origins}},
        methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-API-Token"],
    )


def _setup_rate_limiter(app: Flask) -> None:
    """
    Set up rate limiting.

    Args:
        app: Flask application
    """
    # Configure rate limiting using the utility function
    configure_rate_limiting(app)


def _setup_request_logging(app: Flask) -> None:
    """
    Set up request logging and timing.

    Args:
        app: Flask application
    """

    @app.before_request
    def before_request() -> None:
        """Record request start time."""
        g.start_time = time.time()

    @app.after_request
    def after_request(response: Any) -> Any:
        """Log request details and timing."""
        if hasattr(g, "start_time"):
            duration = round((time.time() - g.start_time) * 1000, 2)
            log_data = {
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_ms": duration,
                "ip": request.remote_addr,
                "user_agent": request.user_agent.string
                if request.user_agent
                else "Unknown",
            }

            # Log differently based on status code
            if response.status_code >= 500:
                current_app.logger.error(f"Request: {log_data}")
            elif response.status_code >= 400:
                current_app.logger.warning(f"Request: {log_data}")
            else:
                current_app.logger.info(f"Request: {log_data}")

        return response


def _setup_security_headers(app: Flask) -> None:
    """
    Set up security headers.

    Args:
        app: Flask application
    """

    @app.after_request
    def add_security_headers(response: Any) -> Any:
        """Add security headers to response."""
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Enable XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Set strict transport security
        response.headers[
            "Strict-Transport-Security"
        ] = "max-age=31536000; includeSubDomains"

        # Content security policy
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response
