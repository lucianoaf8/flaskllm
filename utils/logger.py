# flaskllm/utils/logger.py
"""
Logging Utility Module

This module provides enhanced logging functionality with structured logging support,
custom formatters, and integration with various logging backends.
"""

import logging
import json
from typing import Any, Dict, Optional, Union

# Define log levels
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL


class StructuredFormatter(logging.Formatter):
    """
Custom formatter for structured logging output.

Formats logs as JSON for easier parsing by log management systems.
    """
    def __init__(self, include_timestamp: bool = True):
        """
        Initialize the formatter.
        
        Args:
            include_timestamp: Whether to include a timestamp in the logs
        """
        super().__init__()
        self.include_timestamp = include_timestamp

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log message
        """
        log_data = {
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Include timestamp if requested
        if self.include_timestamp:
            log_data['timestamp'] = self.formatTime(record, '%Y-%m-%d %H:%M:%S')
            
        # Include extra data if present
        if hasattr(record, 'data') and record.data:
            log_data.update(record.data)
            
        # Format traceback if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)


class StructuredLoggerAdapter(logging.LoggerAdapter):
    """
Adapter for adding structured data to log messages.
    """
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """
        Process the logging message and keyword arguments.
        
        Args:
            msg: Log message
            kwargs: Keyword arguments for the logger
            
        Returns:
            Tuple of (message, kwargs)
        """
        # Extract extra data from kwargs
        data = kwargs.pop('extra', {}) if 'extra' in kwargs else {}
        
        # Add additional data from direct keyword arguments
        for key, value in list(kwargs.items()):
            if key not in ('exc_info', 'stack_info', 'stacklevel'):
                data[key] = value
                kwargs.pop(key)
        
        # Update the extra field with our structured data
        kwargs['extra'] = {'data': data}
        
        return msg, kwargs


def get_structured_logger(
    name: str,
    level: int = logging.INFO,
    format_as_json: bool = True,
    include_timestamp: bool = True,
) -> logging.Logger:
    """
    Get a logger configured for structured logging.
    
    Args:
        name: Logger name
        level: Logging level
        format_as_json: Whether to format logs as JSON
        include_timestamp: Whether to include timestamps in logs
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers if any
    for handler in logger.handlers[:]:  
        logger.removeHandler(handler)
    
    # Configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # Set formatter based on configuration
    if format_as_json:
        formatter = StructuredFormatter(include_timestamp=include_timestamp)
    else:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s' \
            if include_timestamp else '%(name)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(log_format)
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Wrap with adapter for structured logging
    return StructuredLoggerAdapter(logger, {})


def configure_app_logging(app, level: int = logging.INFO) -> None:
    """
    Configure logging for a Flask application.
    
    Args:
        app: Flask application instance
        level: Logging level
    """
    # Configure the Flask app logger
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    handler.setLevel(level)
    
    app.logger.handlers = [handler]
    app.logger.setLevel(level)
    
    # Set the log level for Werkzeug
    logging.getLogger('werkzeug').setLevel(level)
