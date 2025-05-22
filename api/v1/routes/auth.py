"""
Authentication API Routes

This module provides API routes for authentication and token management, including:
- Token validation
- Token creation and rotation
- Authentication decorators
- Google OAuth integration
"""
from datetime import datetime
from functools import wraps
from typing import Dict, List, Optional, Callable, Any

from flask import Blueprint, Response, current_app, jsonify, request
from api.v1.schemas.auth import TokenRequest, AuthResponse
from core.auth import validate_token, generate_token, TokenScope
from core.exceptions import AuthenticationError, InvalidInputError
from core.logging import get_logger
from integrations.google_auth import GoogleAuthHandler

# Create a blueprint for the auth routes
bp = Blueprint('auth', __name__, url_prefix='/auth')

# Initialize logger
logger = get_logger(__name__)

# Authentication decorators
def token_required(func: Callable) -> Callable:
    """
    Decorator for routes that require token authentication.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function
        
    Raises:
        AuthenticationError: If authentication fails
    """
    @wraps(func)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        # Get token from request
        token = request.headers.get('X-API-Token')
        if not token:
            logger.warning(
                "Authentication failed: No token provided",
                path=request.path,
                method=request.method,
                remote_addr=request.remote_addr,
            )
            return jsonify({"error": "API token is required"}), 401
            
        # Get the expected token from app config
        settings = current_app.config.get("SETTINGS")
        expected_token = getattr(settings, "api_token", None)
        
        if not expected_token:
            logger.error("API token not configured in settings")
            return jsonify({"error": "Authentication configuration error"}), 500
        
        # Validate token
        if not validate_token(token, expected_token):
            logger.warning(
                "Authentication failed: Invalid token",
                path=request.path,
                method=request.method,
                remote_addr=request.remote_addr,
            )
            return jsonify({"error": "Invalid API token"}), 401
            
        return func(*args, **kwargs)
    
    return decorated

def admin_required(func: Callable) -> Callable:
    """
    Decorator for routes that require admin privileges.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function
        
    Raises:
        AuthenticationError: If authentication fails
    """
    @wraps(func)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        # First check token authentication
        token = request.headers.get('X-API-Token')
        if not token:
            logger.warning(
                "Admin authentication failed: No token provided",
                path=request.path,
                method=request.method,
                remote_addr=request.remote_addr,
            )
            return jsonify({"error": "API token is required"}), 401
        
        # Get the admin token from app config
        settings = current_app.config.get("SETTINGS")
        admin_token = getattr(settings, "admin_token", None)
        
        if not admin_token:
            logger.error("Admin token not configured in settings")
            return jsonify({"error": "Authentication configuration error"}), 500
        
        # Validate admin token
        if not validate_token(token, admin_token):
            logger.warning(
                "Admin authentication failed: Invalid token",
                path=request.path,
                method=request.method,
                remote_addr=request.remote_addr,
            )
            return jsonify({"error": "Invalid admin token"}), 403
            
        return func(*args, **kwargs)
    
    return decorated

# Token management routes
@bp.route('/tokens', methods=['GET'])
@admin_required
def list_tokens():
    """
    List all tokens.
    
    This endpoint requires admin scope.
    """
    token_service = current_app.config.get("TOKEN_SERVICE")
    if not token_service:
        return jsonify({"error": "Token service not configured"}), 500
        
    tokens = token_service.list_tokens()
    
    # Don't include token values in the response
    token_data = []
    for token in tokens:
        data = token.to_dict()
        data["token_value"] = "****" + data["token_value"][-4:] if data["token_value"] else None
        token_data.append(data)
    
    return jsonify({"tokens": token_data}), 200

@bp.route('/tokens', methods=['POST'])
@admin_required
def create_token():
    """
    Create a new token.
    
    This endpoint requires admin scope.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400
    
    description = data.get("description")
    if not description:
        return jsonify({"error": "Token description is required"}), 400
    
    # Parse scopes
    scope = []
    scope_names = data.get("scope", ["read", "write"])
    for scope_name in scope_names:
        try:
            scope.append(TokenScope(scope_name))
        except ValueError:
            return jsonify({"error": f"Invalid scope: {scope_name}"}), 400
    
    # Parse expiration
    expires_in_days = data.get("expires_in_days")
    
    token_service = current_app.config.get("TOKEN_SERVICE")
    if not token_service:
        return jsonify({"error": "Token service not configured"}), 500
        
    token = token_service.create_token(
        description=description,
        scope=scope,
        expires_in_days=expires_in_days
    )
    
    # Include the full token value only when creating
    token_data = token.to_dict()
    
    logger.info(f"Created token: {token.token_id}")
    
    return jsonify({"token": token_data}), 201

@bp.route('/tokens/<token_id>', methods=['GET'])
@admin_required
def get_token(token_id: str):
    """
    Get a token by ID.
    
    This endpoint requires admin scope.
    """
    token_service = current_app.config.get("TOKEN_SERVICE")
    if not token_service:
        return jsonify({"error": "Token service not configured"}), 500
        
    token = token_service.get_token(token_id)
    
    if not token:
        return jsonify({"error": "Token not found"}), 404
    
    # Don't include token value in the response
    token_data = token.to_dict()
    token_data["token_value"] = "****" + token_data["token_value"][-4:] if token_data["token_value"] else None
    
    return jsonify({"token": token_data}), 200

@bp.route('/tokens/<token_id>', methods=['DELETE'])
@admin_required
def revoke_token(token_id: str):
    """
    Revoke a token.
    
    This endpoint requires admin scope.
    """
    token_service = current_app.config.get("TOKEN_SERVICE")
    if not token_service:
        return jsonify({"error": "Token service not configured"}), 500
        
    success = token_service.revoke_token(token_id)
    
    if not success:
        return jsonify({"error": "Token not found"}), 404
    
    logger.info(f"Revoked token: {token_id}")
    
    return jsonify({"message": "Token revoked successfully"}), 200

@bp.route('/tokens/<token_id>/rotate', methods=['POST'])
@admin_required
def rotate_token(token_id: str):
    """
    Rotate a token.
    
    This endpoint requires admin scope.
    """
    data = request.get_json() or {}
    expiration_days = data.get("expiration_days", 30)
    
    token_service = current_app.config.get("TOKEN_SERVICE")
    if not token_service:
        return jsonify({"error": "Token service not configured"}), 500
        
    new_token = token_service.rotate_token(token_id, expiration_days)
    
    if not new_token:
        return jsonify({"error": "Token not found"}), 404
    
    # Include the full token value only when rotating
    token_data = new_token.to_dict()
    
    logger.info(f"Rotated token: {token_id} -> {new_token.token_id}")
    
    return jsonify({
        "message": "Token rotated successfully",
        "old_token_id": token_id,
        "new_token": token_data
    }), 200

# Google OAuth integration
@bp.route('/google/auth', methods=['GET'])
@token_required
def google_auth():
    """
    Initiate Google OAuth flow.
    
    Returns:
        Redirect to Google OAuth authorization URL
    """
    # Get user ID from authentication
    user_id = request.headers.get('X-API-Token')
    
    # Get Google auth handler
    google_auth_handler = GoogleAuthHandler(current_app.config.get("SETTINGS"))
    
    # Get authorization URL
    auth_url = google_auth_handler.get_authorization_url(user_id)
    
    # Redirect to authorization URL
    return jsonify({"auth_url": auth_url}), 200

@bp.route('/google/callback', methods=['GET'])
def google_auth_callback():
    """
    Handle Google OAuth callback.
    
    Returns:
        Success message or error
    """
    # Get authorization code from query parameters
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code or not state:
        return jsonify({"error": "Missing authorization code or state"}), 400
    
    # Get Google auth handler
    google_auth_handler = GoogleAuthHandler(current_app.config.get("SETTINGS"))
    
    # Exchange code for token
    try:
        user_id = google_auth_handler.extract_user_id_from_state(state)
        google_auth_handler.exchange_code_for_token(code, user_id)
        return jsonify({"message": "Successfully authenticated with Google"}), 200
    except Exception as e:
        logger.error(f"Google auth callback error: {str(e)}")
        return jsonify({"error": f"Authentication error: {str(e)}"}), 500

@bp.route('/google/revoke', methods=['POST'])
@token_required
def revoke_google_auth():
    """
    Revoke Google OAuth access.
    
    Returns:
        Success message or error
    """
    # Get user ID from authentication
    user_id = request.headers.get('X-API-Token')
    
    # Get Google auth handler
    google_auth_handler = GoogleAuthHandler(current_app.config.get("SETTINGS"))
    
    # Revoke access
    try:
        google_auth_handler.revoke_access(user_id)
        return jsonify({"message": "Successfully revoked Google access"}), 200
    except Exception as e:
        logger.error(f"Google auth revoke error: {str(e)}")
        return jsonify({"error": f"Revocation error: {str(e)}"}), 500
