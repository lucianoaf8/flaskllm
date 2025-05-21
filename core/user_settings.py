from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from uuid import uuid4

from pydantic import BaseModel, Field

class LLMSettings(BaseModel):
    """LLM settings for a user."""
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)

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
    
    def set_preference(self, key: str, value: Any, category: Optional[str] = None) -> None:
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
                self.updated_at = datetime.utcnow()
                return True
        return False
