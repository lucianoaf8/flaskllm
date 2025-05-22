# core/settings/storage.py
"""
User Settings Storage Module

This module provides storage functionality for user settings, supporting both
in-memory storage and file-based persistence with JSON serialization. It handles
the loading, saving, and management of user-specific settings across application sessions.

The main functionality includes:
- Loading settings from file or creating new ones if they don't exist
- Saving settings to file for persistence
- Managing user settings in memory during application runtime
- Retrieving and deleting user settings
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Set

try:
    import portalocker
    HAS_PORTALOCKER = True
except ImportError:
    HAS_PORTALOCKER = False

from ..exceptions import APIError
from ..logging import get_logger
from .models import UserSettings

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
                    logger.info(f"Creating new settings for user {user_id}: {str(e)}")
                    # Create new settings
                    self.settings[user_id] = UserSettings(user_id=user_id)
            else:
                # Create new settings
                self.settings[user_id] = UserSettings(user_id=user_id)

        return self.settings[user_id]
        
    def has_settings(self, user_id: str) -> bool:
        """
        Check if settings exist for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if settings exist, False otherwise
        """
        # Check in-memory cache first
        if user_id in self.settings:
            return True
            
        # Check file storage if available
        if self.storage_dir:
            file_path = os.path.join(self.storage_dir, f"{user_id}.json")
            return os.path.exists(file_path)
            
        return False
        
    def get_all_user_ids(self) -> List[str]:
        """
        Get a list of all user IDs with saved settings.
        
        Returns:
            List of user IDs
        """
        user_ids = set(self.settings.keys())
        
        # Add users from file storage
        if self.storage_dir and os.path.exists(self.storage_dir):
            for filename in os.listdir(self.storage_dir):
                if filename.endswith(".json"):
                    user_id = filename[:-5]  # Remove .json extension
                    user_ids.add(user_id)
                    
        return sorted(list(user_ids))

    def save_settings(self, settings: UserSettings) -> None:
        """
        Save settings for a user.

        Args:
            settings: User settings
            
        Raises:
            APIError: If settings could not be saved to file
        """
        # Update in memory
        self.settings[settings.user_id] = settings

        # Save to file
        if self.storage_dir:
            try:
                self._save_settings(settings)
            except Exception as e:
                logger.error(f"Error saving settings for user {settings.user_id}: {str(e)}")
                raise APIError(f"Could not save settings: {str(e)}")
                
    def delete_settings(self, user_id: str) -> bool:
        """
        Delete settings for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if settings were deleted, False if they didn't exist
            
        Raises:
            APIError: If settings could not be deleted from file
        """
        # Remove from memory
        if user_id in self.settings:
            del self.settings[user_id]
        else:
            # Check if exists in file storage
            if not self.has_settings(user_id):
                return False
        
        # Remove from file storage
        if self.storage_dir:
            file_path = os.path.join(self.storage_dir, f"{user_id}.json")
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted settings for user {user_id}")
                except Exception as e:
                    logger.error(f"Error deleting settings for user {user_id}: {str(e)}")
                    raise APIError(f"Could not delete settings: {str(e)}")
        
        return True

    def _save_settings(self, settings: UserSettings) -> None:
        """
        Save settings to file.

        Args:
            settings: User settings
            
        Raises:
            Exception: If an error occurs during saving
        """
        if not self.storage_dir:
            return

        file_path = os.path.join(self.storage_dir, f"{settings.user_id}.json")
        temp_path = f"{file_path}.tmp"

        # Update timestamp before saving
        settings.update_timestamp()
        
        # Get serializable dict using UserSettings.to_dict()
        data = settings.to_dict()
        
        # Convert datetime objects to strings
        data["created_at"] = data["created_at"].isoformat()
        data["updated_at"] = data["updated_at"].isoformat()

        # Write to a temporary file first, then rename for atomicity
        try:
            # Use file locking if available
            if HAS_PORTALOCKER:
                with open(temp_path, "w") as f:
                    portalocker.lock(f, portalocker.LOCK_EX)
                    json.dump(data, f, indent=2)
            else:
                with open(temp_path, "w") as f:
                    json.dump(data, f, indent=2)
                    
            # Rename to target file (atomic on most file systems)
            os.replace(temp_path, file_path)
            logger.debug(f"Saved settings for user {settings.user_id}")
        except Exception as e:
            # Clean up temp file if it exists
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            raise

    def _load_settings(self, user_id: str) -> None:
        """
        Load settings from file.

        Args:
            user_id: User ID

        Raises:
            FileNotFoundError: If the settings file is not found
            Exception: If an error occurs during loading
        """
        if not self.storage_dir:
            raise FileNotFoundError(f"Storage directory not configured")

        file_path = os.path.join(self.storage_dir, f"{user_id}.json")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Settings file not found: {file_path}")

        try:
            # Read from file with locking if available
            if HAS_PORTALOCKER:
                with open(file_path, "r") as f:
                    portalocker.lock(f, portalocker.LOCK_SH)
                    data = json.load(f)
            else:
                with open(file_path, "r") as f:
                    data = json.load(f)

            # Convert string timestamps to datetime
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])

            # Create settings using from_dict
            settings = UserSettings.from_dict(data)
            self.settings[user_id] = settings

            logger.debug(f"Loaded settings for user {user_id}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in settings file for user {user_id}: {str(e)}")
            raise APIError(f"Settings file contains invalid JSON: {str(e)}") 
        except Exception as e:
            logger.error(f"Error loading settings for user {user_id}: {str(e)}")
            raise
