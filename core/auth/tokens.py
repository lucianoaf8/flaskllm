# core/auth/tokens.py
import secrets
import string
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import uuid4

from ..exceptions import InvalidInputError
from ..logging import get_logger

logger = get_logger(__name__)

class TokenScope(str, Enum):
    """Scope for API tokens."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

class TokenModel:
    """API token model."""
    
    def __init__(
        self,
        token_value: str,
        description: str,
        scope: List[TokenScope] = None,
        created_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
        token_id: Optional[str] = None,
    ):
        """
        Initialize a new token.
        
        Args:
            token_value: The actual token value
            description: Description of the token's purpose
            scope: List of token scopes
            created_at: Creation timestamp
            expires_at: Expiration timestamp
            token_id: Unique token identifier
        """
        self.token_id = token_id or str(uuid4())
        self.token_value = token_value
        self.description = description
        self.scope = scope or [TokenScope.READ, TokenScope.WRITE]
        self.created_at = created_at or datetime.utcnow()
        self.expires_at = expires_at
        self.last_used_at = None
    
    @property
    def is_expired(self) -> bool:
        """Check if the token is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_admin(self) -> bool:
        """Check if the token has admin scope."""
        return TokenScope.ADMIN in self.scope
    
    def has_scope(self, scope: TokenScope) -> bool:
        """Check if the token has the specified scope."""
        return scope in self.scope
    
    def update_last_used(self) -> None:
        """Update the last used timestamp."""
        self.last_used_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert the token to a dictionary."""
        return {
            "token_id": self.token_id,
            "token_value": self.token_value,
            "description": self.description,
            "scope": [s.value for s in self.scope],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TokenModel":
        """Create a token from a dictionary."""
        scope = [TokenScope(s) for s in data.get("scope", [])]
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        expires_at = datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
        
        token = cls(
            token_value=data["token_value"],
            description=data["description"],
            scope=scope,
            created_at=created_at,
            expires_at=expires_at,
            token_id=data.get("token_id"),
        )
        
        if data.get("last_used_at"):
            token.last_used_at = datetime.fromisoformat(data["last_used_at"])
        
        return token


class TokenService:
    """
    Service for managing API tokens.
    
    This class provides methods for creating, validating, and managing API tokens.
    """
    
    def __init__(self, storage):
        """
        Initialize the token service.
        
        Args:
            storage: Token storage instance
        """
        self.storage = storage
    
    def generate_token_value(self, length: int = 48) -> str:
        """
        Generate a secure random token value.
        
        Args:
            length: Length of the token
            
        Returns:
            Secure random token
        """
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def create_token(
        self, 
        description: str, 
        scope: List[TokenScope] = None,
        expires_in_days: Optional[int] = None,
        token_value: Optional[str] = None
    ) -> TokenModel:
        """
        Create a new token.
        
        Args:
            description: Description of the token's purpose
            scope: List of token scopes
            expires_in_days: Number of days until the token expires
            token_value: Custom token value (generated if not provided)
            
        Returns:
            The created token
        """
        # Generate token value if not provided
        if not token_value:
            token_value = self.generate_token_value()
        
        # Set expiration date if provided
        expires_at = None
        if expires_in_days is not None:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Create the token
        token = TokenModel(
            token_value=token_value,
            description=description,
            scope=scope,
            expires_at=expires_at
        )
        
        # Store the token
        self.storage.add_token(token)
        logger.info(f"Created token: {token.token_id}", token_id=token.token_id)
        
        return token
    
    def validate_token(self, token_value: str) -> Optional[TokenModel]:
        """
        Validate a token and update its last used timestamp.
        
        Args:
            token_value: The token value to validate
            
        Returns:
            The token if valid, None otherwise
        """
        # Find the token by value
        token = self.storage.get_token_by_value(token_value)
        
        # Check if the token exists and is not expired
        if token and not token.is_expired:
            # Update last used timestamp
            token.update_last_used()
            self.storage.update_token(token)
            return token
        
        return None
    
    def revoke_token(self, token_id: str) -> bool:
        """
        Revoke a token.
        
        Args:
            token_id: ID of the token to revoke
            
        Returns:
            True if the token was revoked, False otherwise
        """
        return self.storage.delete_token(token_id)
    
    def list_tokens(self) -> List[TokenModel]:
        """
        List all tokens.
        
        Returns:
            List of all tokens
        """
        return self.storage.list_tokens()
    
    def get_token(self, token_id: str) -> Optional[TokenModel]:
        """
        Get a token by ID.
        
        Args:
            token_id: The token ID
            
        Returns:
            The token if found, None otherwise
        """
        return self.storage.get_token(token_id)
    
    def rotate_token(self, token_id: str, expiration_days: int = 30) -> Optional[TokenModel]:
        """
        Rotate a token by creating a new one and marking the old one for expiration.
        
        Args:
            token_id: ID of the token to rotate
            expiration_days: Number of days until the old token expires
            
        Returns:
            The new token if rotation was successful, None otherwise
        """
        # Get the old token
        old_token = self.storage.get_token(token_id)
        if not old_token:
            return None
        
        # Create a new token with the same scope and description
        new_token = self.create_token(
            description=f"Rotated from {old_token.description}",
            scope=old_token.scope
        )
        
        # Mark the old token for expiration
        old_token.expires_at = datetime.utcnow() + timedelta(days=expiration_days)
        self.storage.update_token(old_token)
        
        logger.info(
            f"Rotated token {old_token.token_id} to {new_token.token_id}",
            old_token_id=old_token.token_id,
            new_token_id=new_token.token_id
        )
        
        return new_token
    
    def migrate_legacy_token(self, legacy_token: str, description: str = "Legacy API token") -> TokenModel:
        """
        Migrate a legacy token to the new token system.
        
        Args:
            legacy_token: The legacy token value
            description: Description for the token
            
        Returns:
            The migrated token
        """
        # Check if the token already exists
        existing_token = self.storage.get_token_by_value(legacy_token)
        if existing_token:
            return existing_token
        
        # Create a new token with the legacy value
        token = self.create_token(
            description=description,
            token_value=legacy_token,
            scope=[TokenScope.READ, TokenScope.WRITE]  # Give legacy tokens full access
        )
        
        logger.info(f"Migrated legacy token to new system: {token.token_id}")
        
        return token
