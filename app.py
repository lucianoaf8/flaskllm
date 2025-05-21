#!/usr/bin/env python3
# app.py
"""
Main application factory for FlaskLLM API.
Creates and configures the Flask application.
"""
from typing import Optional
from flask import Flask

from core.config import get_settings, Settings
from core.logging import configure_logging
from core.middleware import setup_middleware
from api import create_api_blueprint
from core.exceptions import setup_error_handlers


def create_app(settings: Optional[Settings] = None) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        settings: Optional Settings object. If not provided, settings are loaded
                 from environment variables.

    Returns:
        Configured Flask application
    """
    if settings is None:
        settings = get_settings()

    app = Flask(__name__)
    app.config.from_object(settings)

    # Setup logging
    configure_logging(app)

    # Setup middleware
    setup_middleware(app)

    # Register API blueprint
    app.register_blueprint(create_api_blueprint())

    # Register error handlers
    setup_error_handlers(app)

    app.logger.info("Application initialized successfully")
    return app


if __name__ == "__main__":
    # Development server entry point
    app = create_app()
    app.run(debug=True, port=5000)
