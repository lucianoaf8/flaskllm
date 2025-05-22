# flaskllm/api/v1/__init__.py
"""API v1 Blueprint Module

This module defines and creates the Flask blueprint for v1 API endpoints with Swagger
documentation. It serves as the central registration point for all v1 API routes and
provides the base URL prefix '/v1' for the API.

The blueprint uses flask_restx for automatic Swagger documentation generation and
API input/output validation. Authentication is handled via an API key provided in
the X-API-Token header.

Endpoints defined in this API version include:
- LLM prompt processing
- Health checks
- User settings management
- File uploads and processing
- Conversation management
"""
import logging
from typing import Optional

from flask import Blueprint
from flask_restx import Api

# Import at module level to avoid potential circular imports
from api.v1.routes import register_routes


def create_v1_blueprint(api_version: str = "1.0.0") -> Blueprint:
    """
    Create the v1 API blueprint with Swagger documentation.
    
    This function creates a Flask blueprint for the v1 API, configures
    flask_restx for Swagger documentation, and registers all routes
    defined in the routes module.
    
    Args:
        api_version: The API version string to display in Swagger docs
        
    Returns:
        Flask blueprint for v1 API
        
    Raises:
        RuntimeError: If route registration fails
    """
    v1_bp: Blueprint = Blueprint("v1", __name__, url_prefix="/v1")
    
    # Create Flask-RESTX API instance with Swagger docs
    api: Api = Api(
        v1_bp,
        version=api_version,
        title="FlaskLLM API",
        description="A secure, scalable API for processing prompts with LLMs",
        doc="/docs",
        authorizations={
            'apikey': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'X-API-Token'
            }
        },
        security='apikey'
    )
    
    # Register all routes with the API
    try:
        register_routes(api)
        logging.info(f"Successfully registered routes for API v{api_version}")
    except Exception as e:
        logging.error(f"Failed to register routes: {str(e)}")
        raise RuntimeError(f"Failed to initialize API v{api_version}: {str(e)}") from e
    
    return v1_bp