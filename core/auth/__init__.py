from .handlers import auth_required, validate_token, get_token_from_request
from .tokens import TokenService, TokenModel, TokenScope
from .storage import TokenStorage

# Create convenience function for token generation
def generate_token(description: str, scope=None, expires_in_days=None):
    """
    Generate a new token with the given description and scope.
    
    Args:
        description: Description of the token's purpose
        scope: List of token scopes (defaults to read scope)
        expires_in_days: Number of days until token expiration (None for no expiration)
        
    Returns:
        A new TokenModel instance
    """
    # Default to read-only scope if none provided
    if scope is None:
        scope = [TokenScope.READ]
    
    # Get token service from the default storage
    from .storage import get_default_token_storage
    token_service = TokenService(get_default_token_storage())
    
    # Create and return the token
    return token_service.create_token(
        description=description,
        scope=scope,
        expires_in_days=expires_in_days
    )

__all__ = [
    'auth_required', 'validate_token', 'get_token_from_request', 
    'TokenService', 'TokenModel', 'TokenStorage', 'TokenScope',
    'generate_token'
]
