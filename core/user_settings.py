# flaskllm/core/user_settings.py
"""
User Settings Module

This module defines data models for storing and managing user-specific settings
and preferences using Pydantic. These models provide structured storage, validation,
and manipulation of configuration options that can be customized per user.

The main components are:
- LLMSettings: Model-specific settings for LLM interactions
- UISettings: User interface customization options
- Preference: Individual user preference key-value pairs
- UserSettings: Container for all user settings with helper methods
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union, ClassVar

from pydantic import BaseModel, Field, validator


class LLMSettings(BaseModel):
    """LLM settings for a user."""

    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('temperature')
    def validate_temperature(cls, v):
        """Validate that temperature is between 0 and 2."""
        if v is not None and (v < 0 or v > 2):
            raise ValueError('Temperature must be between 0 and 2')
        return v
        
    @validator('max_tokens')
    def validate_max_tokens(cls, v):
        """Validate that max_tokens is positive."""
        if v is not None and v <= 0:
            raise ValueError('Max tokens must be greater than 0')
        return v


class UISettings(BaseModel):
    """UI settings for a user."""

    theme: Optional[str] = None
    font_size: Optional[int] = None
    show_word_count: Optional[bool] = None
    show_token_count: Optional[bool] = None
    default_prompt_type: Optional[str] = None


class Preference(BaseModel):
    """User preference."""

    key: str
    value: Any
    category: Optional[str] = None


class UserSettings(BaseModel):
    """User settings and preferences."""

    user_id: str
    llm_settings: LLMSettings = Field(default_factory=LLMSettings)
    ui_settings: UISettings = Field(default_factory=UISettings)
    preferences: List[Preference] = Field(default_factory=list)
    favorite_templates: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Fields to exclude from serialization for security/privacy
    PRIVATE_FIELDS: ClassVar[List[str]] = []

    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        Get a preference value.

        Args:
            key: Preference key
            default: Default value if not found

        Returns:
            Preference value or default
        """
        for pref in self.preferences:
            if pref.key == key:
                return pref.value
        return default

    def set_preference(
        self, key: str, value: Any, category: Optional[str] = None
    ) -> None:
        """
        Set a preference value.

        Args:
            key: Preference key
            value: Preference value
            category: Preference category
        """
        # Check if preference already exists
        for pref in self.preferences:
            if pref.key == key:
                pref.value = value
                if category:
                    pref.category = category
                self.updated_at = datetime.utcnow()
                return

        # Add new preference
        self.preferences.append(Preference(key=key, value=value, category=category))
        self.updated_at = datetime.utcnow()

    def delete_preference(self, key: str) -> bool:
        """
        Delete a preference.

        Args:
            key: Preference key

        Returns:
            True if deleted, False if not found
        """
        for i, pref in enumerate(self.preferences):
            if pref.key == key:
                del self.preferences[i]
                self.update_timestamp()
                return True
        return False
        
    def update_timestamp(self) -> None:
        """
        Update the updated_at timestamp to current UTC time.
        Call this method whenever the settings are modified.
        """
        self.updated_at = datetime.utcnow()
        
    def to_dict(self, exclude_private: bool = True) -> Dict[str, Any]:
        """
        Convert settings to a dictionary for storage.
        
        Args:
            exclude_private: Whether to exclude private fields
            
        Returns:
            Dictionary representation of settings
        """
        data = self.dict()
        if exclude_private and self.PRIVATE_FIELDS:
            for field in self.PRIVATE_FIELDS:
                if field in data:
                    data.pop(field)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSettings':
        """
        Create settings from a dictionary.
        
        Args:
            data: Dictionary data
            
        Returns:
            UserSettings instance
        """
        return cls(**data)
