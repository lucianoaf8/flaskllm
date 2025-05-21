import json
import os
from datetime import datetime
from typing import Dict, Optional

from core.exceptions import SettingsError
from core.logging import get_logger
from core.user_settings import UserSettings

logger = get_logger(__name__)

class UserSettingsStorage:
    """
    Storage for user settings.
    
    Supports in-memory storage and file-based persistence.
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize the user settings storage.
        
        Args:
            storage_dir: Directory for file-based storage
        """
        self.settings: Dict[str, UserSettings] = {}
        self.storage_dir = storage_dir
        
        # Create storage directory if it doesn't exist
        if storage_dir and not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
            logger.info(f"Created user settings storage directory: {storage_dir}")
    
    def get_settings(self, user_id: str) -> UserSettings:
        """
        Get settings for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            User settings
        """
        if user_id not in self.settings:
            # Try to load from file
            if self.storage_dir:
                try:
                    self._load_settings(user_id)
                except Exception as e:
                    # Create new settings
                    self.settings[user_id] = UserSettings(user_id=user_id)
            else:
                # Create new settings
                self.settings[user_id] = UserSettings(user_id=user_id)
        
        return self.settings[user_id]
    
    def save_settings(self, settings: UserSettings) -> None:
        """
        Save settings for a user.
        
        Args:
            settings: User settings
        """
        # Update in memory
        self.settings[settings.user_id] = settings
        
        # Save to file
        self._save_settings(settings)
    
    def _save_settings(self, settings: UserSettings) -> None:
        """
        Save settings to file.
        
        Args:
            settings: User settings
        """
        if not self.storage_dir:
            return
        
        file_path = os.path.join(self.storage_dir, f"{settings.user_id}.json")
        
        try:
            # Convert to JSON-serializable dict
            data = settings.dict()
            
            # Convert datetime objects to strings
            data['created_at'] = data['created_at'].isoformat()
            data['updated_at'] = data['updated_at'].isoformat()
            
            # Write to file
            with open(file_path, 'w') as f:
                json.dump(data, f)
            
            logger.debug(f"Saved settings for user {settings.user_id}")
        except Exception as e:
            logger.error(f"Error saving settings for user {settings.user_id}: {str(e)}")
    
    def _load_settings(self, user_id: str) -> None:
        """
        Load settings from file.
        
        Args:
            user_id: User ID
            
        Raises:
            FileNotFoundError: If the settings file is not found
        """
        if not self.storage_dir:
            raise FileNotFoundError(f"Storage directory not configured")
        
        file_path = os.path.join(self.storage_dir, f"{user_id}.json")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Settings file not found: {file_path}")
        
        try:
            # Read from file
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Convert string timestamps to datetime
            data['created_at'] = datetime.fromisoformat(data['created_at'])
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
            
            # Create settings
            settings = UserSettings(**data)
            self.settings[user_id] = settings
            
            logger.debug(f"Loaded settings for user {user_id}")
        except Exception as e:
            logger.error(f"Error loading settings for user {user_id}: {str(e)}")
            raise
