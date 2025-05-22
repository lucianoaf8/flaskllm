# flaskllm/utils/config/loader.py
"""
Configuration Loader Module

This module provides utilities for loading configuration from various sources
including environment variables, JSON files, YAML files, etc.
"""

import os
from typing import Any, Dict, Optional
from core.exceptions import APIError
from core.logging import get_logger

import json
from pathlib import Path
from typing import Union

# Configure logger
logger = get_logger(__name__)


def load_json_config(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Dictionary containing configuration values from the JSON file
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    logger.debug(f"Loading JSON config from {file_path}")
    
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Config file not found: {file_path}")
    
    try:
        with open(file_path, 'r') as file:
            config = json.load(file)
        return config
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON config file {file_path}: {e}")
        raise


def load_env_config(prefix: str = "FLASKLLM_") -> Dict[str, Any]:
    """
    Load configuration from environment variables with the specified prefix.
    
    Args:
        prefix: Prefix for environment variables to include
        
    Returns:
        Dictionary containing configuration values from environment variables
    """
    logger.debug(f"Loading environment config with prefix {prefix}")
    
    config = {}
    
    for key, value in os.environ.items():
        if key.startswith(prefix):
            # Remove prefix and convert to lowercase for consistent keys
            config_key = key[len(prefix):].lower()
            config[config_key] = value
    
    return config


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple configuration dictionaries, with later dictionaries
    taking precedence over earlier ones.
    
    Args:
        *configs: Configuration dictionaries to merge
        
    Returns:
        Merged configuration dictionary
    """
    logger.debug(f"Merging {len(configs)} configuration dictionaries")
    
    result = {}
    
    for config in configs:
        # Deep merge nested dictionaries
        for key, value in config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_configs(result[key], value)
            else:
                result[key] = value
    
    return result


def get_config_value(config: Dict[str, Any], key: str, default: Optional[Any] = None) -> Any:
    """
    Get a configuration value by key, with support for nested keys using dot notation.
    
    Args:
        config: Configuration dictionary
        key: Configuration key, can use dot notation for nested keys
        default: Default value to return if the key is not found
        
    Returns:
        Configuration value or default if not found
    """
    logger.debug(f"Getting config value for key: {key}")
    
    # Handle nested keys with dot notation
    keys = key.split('.')
    
    # Navigate through nested dictionaries
    current = config
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            logger.debug(f"Config key not found, using default: {key}")
            return default
    
    return current


class ConfigLoader:
    """
    Configuration loader class for handling config from various sources.
    
    Provides unified access to configuration from files, environment variables,
    and default values.
    """
    
    def __init__(self, config_dir: Optional[Union[str, Path]] = None):
        """
        Initialize the configuration loader.
        
        Args:
            config_dir: Directory containing configuration files (optional)
        """
        self.config_dir = Path(config_dir) if config_dir else None
        self.config = {}
        self.logger = logger
    
    def get_config_path(self, filename: str) -> Path:
        """
        Get the full path to a configuration file.
        
        Args:
            filename: Configuration filename
            
        Returns:
            Full path to the configuration file
        
        Raises:
            ValueError: If no config directory is set
        """
        if not self.config_dir:
            raise ValueError("No configuration directory set")
        
        return self.config_dir / filename
    
    def load_json_file(self, filename: str) -> Dict[str, Any]:
        """
        Load configuration from a JSON file in the config directory.
        
        Args:
            filename: JSON configuration filename
            
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If no config directory is set
        """
        file_path = self.get_config_path(filename)
        return load_json_config(file_path)
    
    def load_from_env(self, prefix: str = "FLASKLLM_") -> Dict[str, Any]:
        """
        Load configuration from environment variables.
        
        Args:
            prefix: Prefix for environment variables to include
            
        Returns:
            Configuration dictionary
        """
        return load_env_config(prefix)
    
    def load_config(
        self, 
        json_file: Optional[str] = None, 
        env_prefix: str = "FLASKLLM_",
        defaults: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Load configuration from multiple sources and merge them.
        
        Priority order (highest to lowest):
        1. Environment variables
        2. JSON file
        3. Default values
        
        Args:
            json_file: JSON configuration filename (optional)
            env_prefix: Prefix for environment variables
            defaults: Default configuration values
            
        Returns:
            Merged configuration dictionary
        """
        config_sources = []
        
        # Add defaults if provided
        if defaults:
            config_sources.append(defaults)
        
        # Add JSON config if specified
        if json_file:
            try:
                json_config = self.load_json_file(json_file)
                config_sources.append(json_config)
            except FileNotFoundError:
                self.logger.warning(f"Config file not found: {json_file}")
            except json.JSONDecodeError:
                self.logger.error(f"Invalid JSON in config file: {json_file}")
        
        # Add environment variables
        env_config = self.load_from_env(env_prefix)
        config_sources.append(env_config)
        
        # Merge all configs
        self.config = merge_configs(*config_sources)
        return self.config
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Configuration key (can use dot notation for nested keys)
            default: Default value to return if key not found
            
        Returns:
            Configuration value or default if not found
        """
        return get_config_value(self.config, key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key (can use dot notation for nested keys)
            value: Configuration value to set
        """
        # Handle nested keys with dot notation
        keys = key.split('.')
        
        # Navigate to the correct nested dictionary
        current = self.config
        for i, k in enumerate(keys[:-1]):
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        
        # Set the value
        current[keys[-1]] = value
    
    def update(self, config_dict: Dict[str, Any]) -> None:
        """
        Update configuration with values from a dictionary.
        
        Args:
            config_dict: Dictionary containing configuration values
        """
        self.config = merge_configs(self.config, config_dict)
    
    def as_dict(self) -> Dict[str, Any]:
        """
        Get the entire configuration as a dictionary.
        
        Returns:
            Configuration dictionary
        """
        return self.config.copy()
