# flaskllm/api/v1/__init__.py
"""
API v1 Blueprint Module

This module defines and creates the Flask blueprint for v1 API endpoints.
"""
from flask import Blueprint
from flask_restx import Api

def create_v1_blueprint() -> Blueprint:
    """
    Create the v1 API blueprint with Swagger documentation.

    Returns:
        Flask blueprint for v1 API
    """
    v1_bp = Blueprint("v1", __name__, url_prefix="/v1")
    
    # Create Flask-RESTX API instance with Swagger docs
    api = Api(
        v1_bp,
        version="1.0.0",
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
    
    # Import routes to register them with the API
    from flaskllm.api.v1.routes import register_routes
    register_routes(api)
    
    return v1_bp