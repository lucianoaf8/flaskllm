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


def request_id_contextualizer(logger, method_name, event_dict) -> Dict[str, Any]:
    """
    Add request ID to log context if available.

    Args:
        logger: The logger instance
        method_name: The name of the logging method
        event_dict: The current event dictionary

    Returns:
        Updated event dictionary with request ID
    """
    try:
        if request:
            # Use existing X-Request-ID header or generate a new one
            request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
            event_dict["request_id"] = request_id
    except RuntimeError:
        # In case we're outside a request context
        # Flask raises RuntimeError when request is accessed outside context
        pass
    return event_dict


def configure_logging(app: Optional[Flask] = None, log_level: Optional[int] = None) -> None:
    """
    Configure structured logging for the application.

    Args:
        app: Flask application instance
        log_level: Optional log level (use logging.INFO, logging.DEBUG, etc.)
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

    # Determine if we're in debug mode
    is_debug = False
    if app:
        is_debug = app.config.get("DEBUG", False)
    
    # Add JSON renderer for production, console renderer for development
    if app and not is_debug:
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
    
    # Determine log level
    if log_level is None:
        # Use INFO as default, but respect DEBUG mode
        log_level = logging.DEBUG if is_debug else logging.INFO

    # Configure standard logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        level=log_level,
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

        def custom_start_response(status: str, headers: list, exc_info=None) -> Any:
            try:
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
            except Exception as e:
                # Don't let logging errors affect the response
                self.logger.error("Error in request logging", error=str(e))
                
            return start_response(status, headers, exc_info)

        return self.app(environ, custom_start_response)
