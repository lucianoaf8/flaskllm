"""
Authentication Schema Definitions

This module contains Pydantic schemas for authentication-related operations.
"""
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator

class TokenScope(str, Enum):
    """Scope of a token."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

class TokenRequest(BaseModel):
    """Schema for token creation request."""
    description: str = Field(..., description="Token description")
    scope: Optional[List[TokenScope]] = Field(default=[TokenScope.READ, TokenScope.WRITE], description="Token scopes")
    expires_in_days: Optional[int] = Field(default=30, description="Token expiration in days")

class Token(BaseModel):
    """Schema for an API token."""
    token_id: str = Field(..., description="Token ID")
    token_value: Optional[str] = Field(default=None, description="Token value")
    description: str = Field(..., description="Token description")
    scope: List[TokenScope] = Field(..., description="Token scopes")
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: Optional[datetime] = Field(default=None, description="Expiration timestamp")
    is_active: bool = Field(..., description="Whether the token is active")

class AuthResponse(BaseModel):
    """Schema for authentication response."""
    token: Optional[Token] = Field(default=None, description="Token data")
    message: Optional[str] = Field(default=None, description="Response message")
    error: Optional[str] = Field(default=None, description="Error message")

class GoogleAuthRequest(BaseModel):
    """Schema for Google OAuth request."""
    redirect_uri: Optional[str] = Field(default=None, description="Redirect URI")

class GoogleAuthResponse(BaseModel):
    """Schema for Google OAuth response."""
    auth_url: Optional[str] = Field(default=None, description="Authorization URL")
    message: Optional[str] = Field(default=None, description="Response message")
    error: Optional[str] = Field(default=None, description="Error message")

class UserSettings(BaseModel):
    """Schema for user settings."""
    user_id: str = Field(..., description="User ID")
    theme: Optional[str] = Field(default="light", description="UI theme")
    language: Optional[str] = Field(default="en", description="Language preference")
    notifications_enabled: Optional[bool] = Field(default=True, description="Notifications enabled")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")

class UserSettingsRequest(BaseModel):
    """Schema for user settings update request."""
    theme: Optional[str] = Field(default=None, description="UI theme")
    language: Optional[str] = Field(default=None, description="Language preference")
    notifications_enabled: Optional[bool] = Field(default=None, description="Notifications enabled")
    preferences: Optional[Dict[str, Any]] = Field(default=None, description="User preferences")
