# flaskllm/api/__init__.py
"""
API Blueprint Module

This module defines and creates the Flask blueprint for the API endpoints.
"""
from flask import Blueprint

from api.v1 import create_v1_blueprint


def create_api_blueprint() -> Blueprint:
    """
    Create the API blueprint with versioned endpoints.

    Returns:
        Flask blueprint for the API
    """
    api_bp = Blueprint("api", __name__, url_prefix="/api")

    # Register versioned blueprints
    api_bp.register_blueprint(create_v1_blueprint())

    return api_bp
