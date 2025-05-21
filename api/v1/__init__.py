# flaskllm/api/v1/__init__.py
"""
API v1 Blueprint Module

This module defines and creates the Flask blueprint for v1 API endpoints.
"""
from flask import Blueprint


def create_v1_blueprint() -> Blueprint:
    """
    Create the v1 API blueprint.

    Returns:
        Flask blueprint for v1 API
    """
    v1_bp = Blueprint("v1", __name__, url_prefix="/v1")

    # Import routes to register them with the blueprint
    from api.v1.routes import register_routes

    register_routes(v1_bp)

    return v1_bp
