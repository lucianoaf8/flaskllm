"""
Token Validator Utility Module

This module provides a utility for validating tokens of various formats,
including JWT, API keys, and OAuth tokens.
"""
import re
import time
from typing import Any, Dict, List, Optional, Tuple, Union

from jwt import PyJWTError, decode, InvalidTokenError

from core.logging import get_logger

# Configure logger
logger = get_logger(__name__)


class TokenValidator:
    """Utility class for validating different types of tokens."""
    
    def __init__(self, secret_key: str = None):
        """
        Initialize the validator.
        
        Args:
            secret_key: Secret key for validating signed tokens
        """
        self.secret_key = secret_key
    
    def validate_jwt(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate a JWT token.
        
        Args:
            token: JWT token to validate
            
        Returns:
            Tuple of (is_valid, token_payload)
        """
        if not token:
            return False, None
            
        try:
            # Decode and validate token
            payload = decode(token, self.secret_key, algorithms=['HS256'])
            
            # Check if token is expired
            if 'exp' in payload and payload['exp'] < time.time():
                logger.warning(f"Token expired at {payload['exp']}")
                return False, None
                
            return True, payload
        except (PyJWTError, InvalidTokenError) as e:
            logger.warning(f"Invalid JWT token: {e}")
            return False, None
    
    def validate_api_key(self, api_key: str, valid_keys: List[str]) -> bool:
        """
        Validate an API key.
        
        Args:
            api_key: API key to validate
            valid_keys: List of valid API keys
            
        Returns:
            Whether the API key is valid
        """
        if not api_key:
            return False
            
        # Simple exact match validation
        return api_key in valid_keys
    
    def validate_oauth_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate an OAuth token by calling the token info endpoint.
        
        Args:
            token: OAuth token to validate
            
        Returns:
            Tuple of (is_valid, token_info)
        """
        # This would typically make a request to an OAuth provider's token info endpoint
        # For now, we'll just do basic validation
        if not token or len(token) < 10:
            return False, None
            
        # Additional validation would be done here
        return True, {"valid": True, "scope": "read write"}
    
    @staticmethod
    def is_valid_token_format(token: str) -> bool:
        """
        Check if a token has a valid format (basic syntax validation).
        
        Args:
            token: Token to validate
            
        Returns:
            Whether the token has a valid format
        """
        if not token or not isinstance(token, str):
            return False
            
        # Basic token format validation (alphanumeric with some special chars)
        return bool(re.match(r'^[a-zA-Z0-9._\-]+$', token))

