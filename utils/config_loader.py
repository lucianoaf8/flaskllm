# flaskllm/utils/config_loader.py
"""
Configuration Loader Module

This module provides utilities for loading configuration from various sources
including environment variables, JSON files, YAML files, etc.
"""

import os
import json
from typing import Any, Dict, Optional, Union
from pathlib import Path

from core.logging import get_logger

# Configure logger
logger = get_logger(__name__)


def load_json_config(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        file_path: Path to the JSON configuration file
        
    Returns:
        Dictionary containing configuration values
        
    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    try:
        file_path = Path(file_path)
        logger.info(f"Loading configuration from {file_path}")
        
        with open(file_path, 'r') as f:
            config = json.load(f)
            
        logger.info(f"Successfully loaded configuration from {file_path}")
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file {file_path}: {str(e)}")
        raise


def load_env_config(prefix: str = "FLASKLLM_") -> Dict[str, str]:
    """
    Load configuration from environment variables with the specified prefix.
    
    Args:
        prefix: Prefix for environment variables to include
        
    Returns:
        Dictionary containing configuration values from environment variables
    """
    logger.info(f"Loading configuration from environment variables with prefix {prefix}")
    
    config = {}
    for key, value in os.environ.items():
        if key.startswith(prefix):
            # Remove prefix and convert to lowercase for consistency
            config_key = key[len(prefix):].lower()
            config[config_key] = value
    
    logger.info(f"Loaded {len(config)} configuration values from environment variables")
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
    result: Dict[str, Any] = {}
    
    for config in configs:
        result.update(config)
    
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
    if '.' not in key:
        return config.get(key, default)
    
    parts = key.split('.')
    current = config
    
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            return default
        current = current[part]
    
    return current.get(parts[-1], default)
