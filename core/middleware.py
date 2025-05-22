# flaskllm/core/middleware.py
"""
Middleware for the application.

This module configures and sets up various middleware components for the Flask application,
including CORS, rate limiting, request logging, and security headers.
"""
import time
from typing import Any, Dict, Optional, Callable

from flask import Flask, current_app, g, request, Response
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from core.config import get_settings
from core.logging import get_logger
from utils.rate_limiter import configure_rate_limiting

# Get a structured logger
logger = get_logger(__name__)


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
    
    Note: There is some overlap between this functionality and the RequestLogger
    class in logging.py. Consider using one or the other to avoid duplication.

    Args:
        app: Flask application
    """

    @app.before_request
    def before_request() -> None:
        """Record request start time."""
        g.start_time = time.time()

    @app.after_request
    def after_request(response: Response) -> Response:
        """Log request details and timing using structured logging."""
        if hasattr(g, "start_time"):
            duration = round((time.time() - g.start_time) * 1000, 2)
            
            # Use structured logging instead of f-strings
            user_agent = request.user_agent.string if request.user_agent else "Unknown"
            
            # Log differently based on status code
            if response.status_code >= 500:
                logger.error(
                    "Request failed",
                    method=request.method,
                    path=request.path,
                    status=response.status_code,
                    duration_ms=duration,
                    ip=request.remote_addr,
                    user_agent=user_agent
                )
            elif response.status_code >= 400:
                logger.warning(
                    "Request error",
                    method=request.method,
                    path=request.path,
                    status=response.status_code,
                    duration_ms=duration,
                    ip=request.remote_addr,
                    user_agent=user_agent
                )
            else:
                logger.info(
                    "Request processed",
                    method=request.method,
                    path=request.path,
                    status=response.status_code,
                    duration_ms=duration,
                    ip=request.remote_addr,
                    user_agent=user_agent
                )

        return response


def _setup_security_headers(app: Flask) -> None:
    """
    Set up security headers.

    Args:
        app: Flask application
    """

    @app.after_request
    def add_security_headers(response: Response) -> Response:
        """Add security headers to response."""
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Enable XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Set strict transport security
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

        # Content security policy - less restrictive but still secure
        # Allow self, inline scripts for compatibility, and data URIs
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self' data:; "
            "connect-src 'self'"
        )

        return response
