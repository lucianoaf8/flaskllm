# flaskllm/core/logging.py
"""
Logging Configuration Module

This module configures logging for the application using structlog
for structured logging with consistent formatting.
"""
import logging
import sys
import time
import uuid
from typing import Any, Dict, Optional

import structlog
from flask import Flask, request


def request_id_contextualizer() -> Dict[str, str]:
    """
    Add request ID to log context if available.

    Returns:
        Dictionary with request ID context
    """
    if request:
        # Use existing X-Request-ID header or generate a new one
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        return {"request_id": request_id}
    return {}


def configure_logging(app: Optional[Flask] = None) -> None:
    """
    Configure structured logging for the application.

    Args:
        app: Flask application instance
    """
    # Configure structlog processors
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        request_id_contextualizer,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add JSON renderer for production, console renderer for development
    if app and not app.config.get("DEBUG", False):
        # Use JSON formatter for production
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Use console formatter for development
        processors.append(structlog.dev.ConsoleRenderer(colors=True, sort_keys=False))

    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
        stream=sys.stdout,
    )

    # Set level for other loggers to avoid noise
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a logger with the given name.

    Args:
        name: Logger name, typically __name__

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


class RequestLogger:
    """Middleware for logging HTTP requests and responses."""

    def __init__(self, app: Flask) -> None:
        """
        Initialize RequestLogger middleware.

        Args:
            app: Flask application
        """
        self.app = app
        self.logger = get_logger("flask.request")

    def __call__(self, environ: Dict[str, Any], start_response: Any) -> Any:
        """
        Log request and response details.

        Args:
            environ: WSGI environment
            start_response: WSGI start_response function

        Returns:
            WSGI response
        """
        request_start = time.time()

        def custom_start_response(status, headers, exc_info=None):
            status_code = int(status.split(" ")[0])
            processing_time = (time.time() - request_start) * 1000

            # Log request and response details
            self.logger.info(
                "Request processed",
                method=environ.get("REQUEST_METHOD"),
                path=environ.get("PATH_INFO"),
                query=environ.get("QUERY_STRING"),
                status=status_code,
                processing_time=f"{processing_time:.2f}ms",
                remote_addr=environ.get("REMOTE_ADDR"),
                user_agent=environ.get("HTTP_USER_AGENT", ""),
            )

            return start_response(status, headers, exc_info)

        return self.app(environ, custom_start_response)
