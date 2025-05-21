# flaskllm/utils/security.py
"""
Security Utility Module

This module provides security-related utility functions.
"""
import hashlib
import os
import re
from typing import Any, Dict, List

from flaskllm.core.logging import get_logger

# Configure logger
logger = get_logger(__name__)


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.

    Args:
        length: Length of the token

    Returns:
        Secure random token
    """
    # Use os.urandom for cryptographically secure random bytes
    rand_bytes = os.urandom(length)
    # Convert to URL-safe base64 and remove padding
    token = hashlib.sha256(rand_bytes).hexdigest()[:length]
    return token


def sanitize_string(value: str) -> str:
    """
    Sanitize a string to prevent injection attacks.

    Args:
        value: String to sanitize

    Returns:
        Sanitized string
    """
    # Remove any control characters and ensure UTF-8
    value = "".join(c for c in value if c.isprintable())

    # Remove any HTML or script tags
    value = re.sub(r"<[^>]*>", "", value)

    return value


def sanitize_input(data: Any) -> Any:
    """
    Recursively sanitize input data.

    Args:
        data: Input data to sanitize

    Returns:
        Sanitized data
    """
    if isinstance(data, str):
        return sanitize_string(data)
    elif isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(v) for v in data]
    else:
        return data


def mask_sensitive_data(
    data: Dict[str, Any], sensitive_fields: List[str]
) -> Dict[str, Any]:
    """
    Mask sensitive data in a dictionary for logging.

    Args:
        data: Dictionary containing data
        sensitive_fields: List of sensitive field names to mask

    Returns:
        Dictionary with sensitive data masked
    """
    result = data.copy()

    for field in sensitive_fields:
        if field in result and result[field]:
            if isinstance(result[field], str):
                # Mask all but first and last character
                value = result[field]
                if len(value) > 4:
                    result[field] = f"{value[0]}{'*' * (len(value) - 2)}{value[-1]}"
                else:
                    result[field] = "****"

    return result
