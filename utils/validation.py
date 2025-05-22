# flaskllm/utils/validation.py
"""
Validation Utility Module

This module provides utilities for validating various types of input data,
including strings, numbers, email addresses, URLs, etc.
"""

import re
import ipaddress
from datetime import datetime
from typing import Any, Dict, List, Optional, Pattern, Tuple, Union
from urllib.parse import urlparse

from core.logging import get_logger

# Configure logger
logger = get_logger(__name__)

# Regular expressions for common validation patterns
EMAIL_PATTERN: Pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
USERNAME_PATTERN: Pattern = re.compile(r'^[a-zA-Z0-9_-]{3,32}$')
PASSWORD_PATTERN: Pattern = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
)
IPV4_PATTERN: Pattern = re.compile(r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
DOMAIN_PATTERN: Pattern = re.compile(r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$')


def validate_string(
    value: Any,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    pattern: Optional[Pattern] = None,
    strip: bool = True,
) -> Tuple[bool, Optional[str]]:
    """
    Validate a string value.
    
    Args:
        value: Value to validate
        min_length: Minimum length (inclusive)
        max_length: Maximum length (inclusive)
        pattern: Regular expression pattern to match
        strip: Whether to strip whitespace before validation
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if value is a string
    if not isinstance(value, str):
        return False, "Value must be a string"
    
    # Strip whitespace if requested
    if strip:
        value = value.strip()
    
    # Check minimum length
    if min_length is not None and len(value) < min_length:
        return False, f"Value must be at least {min_length} characters long"
    
    # Check maximum length
    if max_length is not None and len(value) > max_length:
        return False, f"Value must be at most {max_length} characters long"
    
    # Check pattern match
    if pattern is not None and not pattern.match(value):
        return False, "Value does not match the required pattern"
    
    return True, None


def validate_email(value: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate an email address.
    
    Args:
        value: Email address to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # First validate as a string
    is_valid, error_message = validate_string(value, min_length=5, max_length=254)
    if not is_valid:
        return is_valid, error_message
    
    # Check email pattern
    if not EMAIL_PATTERN.match(value):
        return False, "Invalid email address format"
    
    return True, None


def validate_url(
    value: Any,
    required_schemes: Optional[List[str]] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Validate a URL.
    
    Args:
        value: URL to validate
        required_schemes: List of required URL schemes (e.g., ['http', 'https'])
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # First validate as a string
    is_valid, error_message = validate_string(value)
    if not is_valid:
        return is_valid, error_message
    
    try:
        parsed_url = urlparse(value)
        
        # Check if URL has a scheme
        if not parsed_url.scheme:
            return False, "URL must include a scheme (e.g., http://, https://)"
        
        # Check if URL has a netloc (domain)
        if not parsed_url.netloc:
            return False, "URL must include a domain"
        
        # Check if scheme is in required schemes
        if required_schemes and parsed_url.scheme not in required_schemes:
            return False, f"URL scheme must be one of: {', '.join(required_schemes)}"
        
        return True, None
    except Exception as e:
        return False, f"Invalid URL: {str(e)}"


def validate_integer(
    value: Any,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Validate an integer value.
    
    Args:
        value: Value to validate
        min_value: Minimum value (inclusive)
        max_value: Maximum value (inclusive)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if value is an integer or can be converted to one
    try:
        if not isinstance(value, int):
            value = int(value)
    except (ValueError, TypeError):
        return False, "Value must be an integer"
    
    # Check minimum value
    if min_value is not None and value < min_value:
        return False, f"Value must be at least {min_value}"
    
    # Check maximum value
    if max_value is not None and value > max_value:
        return False, f"Value must be at most {max_value}"
    
    return True, None


def validate_float(
    value: Any,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Validate a float value.
    
    Args:
        value: Value to validate
        min_value: Minimum value (inclusive)
        max_value: Maximum value (inclusive)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if value is a float or can be converted to one
    try:
        if not isinstance(value, float):
            value = float(value)
    except (ValueError, TypeError):
        return False, "Value must be a number"
    
    # Check minimum value
    if min_value is not None and value < min_value:
        return False, f"Value must be at least {min_value}"
    
    # Check maximum value
    if max_value is not None and value > max_value:
        return False, f"Value must be at most {max_value}"
    
    return True, None


def validate_boolean(value: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate a boolean value, including string representations.
    
    Args:
        value: Value to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # If already a boolean, it's valid
    if isinstance(value, bool):
        return True, None
    
    # Check string representations
    if isinstance(value, str):
        # Convert to lowercase for comparison
        value_lower = value.lower()
        if value_lower in ('true', 't', 'yes', 'y', '1'):
            return True, None
        if value_lower in ('false', 'f', 'no', 'n', '0'):
            return True, None
    
    # Check integer representations
    if isinstance(value, int) and value in (0, 1):
        return True, None
    
    return False, "Value must be a boolean or a valid boolean string representation"


def validate_date(
    value: Any,
    format_str: str = "%Y-%m-%d",
    min_date: Optional[datetime] = None,
    max_date: Optional[datetime] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Validate a date string.
    
    Args:
        value: Date string to validate
        format_str: Date format string (strftime format)
        min_date: Minimum allowed date
        max_date: Maximum allowed date
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # First validate as a string
    is_valid, error_message = validate_string(value)
    if not is_valid:
        return is_valid, error_message
    
    # Try to parse the date
    try:
        date = datetime.strptime(value, format_str)
        
        # Check minimum date
        if min_date is not None and date < min_date:
            return False, f"Date must be on or after {min_date.strftime(format_str)}"
        
        # Check maximum date
        if max_date is not None and date > max_date:
            return False, f"Date must be on or before {max_date.strftime(format_str)}"
        
        return True, None
    except ValueError:
        return False, f"Invalid date format, expected {format_str}"


def validate_ip_address(value: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate an IP address (IPv4 or IPv6).
    
    Args:
        value: IP address to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # First validate as a string
    is_valid, error_message = validate_string(value)
    if not is_valid:
        return is_valid, error_message
    
    # Try to parse as IP address
    try:
        ipaddress.ip_address(value)
        return True, None
    except ValueError:
        return False, "Invalid IP address"


def validate_dict(
    value: Any,
    required_keys: Optional[List[str]] = None,
    optional_keys: Optional[List[str]] = None,
    allow_extra_keys: bool = False,
) -> Tuple[bool, Optional[str]]:
    """
    Validate a dictionary with required and optional keys.
    
    Args:
        value: Dictionary to validate
        required_keys: List of required keys
        optional_keys: List of optional keys
        allow_extra_keys: Whether to allow keys not in required_keys or optional_keys
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if value is a dictionary
    if not isinstance(value, dict):
        return False, "Value must be a dictionary"
    
    # Check required keys
    if required_keys:
        for key in required_keys:
            if key not in value:
                return False, f"Missing required key: {key}"
    
    # Check for extra keys
    if not allow_extra_keys and (required_keys or optional_keys):
        allowed_keys = set(required_keys or []) | set(optional_keys or [])
        extra_keys = set(value.keys()) - allowed_keys
        if extra_keys:
            return False, f"Unexpected keys: {', '.join(extra_keys)}"
    
    return True, None


def validate_list(
    value: Any,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    item_validator: Optional[callable] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Validate a list.
    
    Args:
        value: List to validate
        min_length: Minimum length of the list
        max_length: Maximum length of the list
        item_validator: Function to validate each item in the list
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if value is a list
    if not isinstance(value, list):
        return False, "Value must be a list"
    
    # Check minimum length
    if min_length is not None and len(value) < min_length:
        return False, f"List must contain at least {min_length} items"
    
    # Check maximum length
    if max_length is not None and len(value) > max_length:
        return False, f"List must contain at most {max_length} items"
    
    # Validate each item if a validator is provided
    if item_validator:
        for i, item in enumerate(value):
            is_valid, error_message = item_validator(item)
            if not is_valid:
                return False, f"Item at index {i} is invalid: {error_message}"
    
    return True, None


def sanitize_string(value: str, allow_html: bool = False) -> str:
    """
    Sanitize a string by removing potentially harmful content.
    
    Args:
        value: String to sanitize
        allow_html: Whether to allow HTML tags
        
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return str(value)
        
    # Strip control characters
    result = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
    
    if not allow_html:
        # Remove HTML tags if not allowed
        result = re.sub(r'<[^>]*>', '', result)
        
    # Remove potential SQL injection patterns
    result = re.sub(r'[\\;\'\"\(\)]', '', result)
    
    return result


def validate_input(
    data: Dict[str, Any],
    schema: Dict[str, Dict[str, Any]],
    strict: bool = True
) -> Tuple[bool, Optional[Dict[str, str]]]:
    """
    Validate input data against a schema.
    
    Args:
        data: Dictionary of input data to validate
        schema: Dictionary defining validation rules for each field
        strict: Whether to fail validation if extra fields are present
        
    Returns:
        Tuple of (is_valid, errors_dict)
    """
    if not isinstance(data, dict):
        return False, {"_general": "Input data must be a dictionary"}
    
    errors = {}
    
    # Check for missing required fields
    for field_name, field_schema in schema.items():
        # Check if field is required
        if field_schema.get("required", False) and field_name not in data:
            errors[field_name] = "This field is required"
    
    # Check for extra fields if strict mode is enabled
    if strict:
        extra_fields = set(data.keys()) - set(schema.keys())
        if extra_fields:
            errors["_extra_fields"] = f"Unexpected fields: {', '.join(extra_fields)}"
    
    # Validate each field
    for field_name, field_value in data.items():
        # Skip fields not in schema if not in strict mode
        if field_name not in schema and not strict:
            continue
            
        # Skip fields not in schema if in strict mode (already reported above)
        if field_name not in schema:
            continue
        
        field_schema = schema[field_name]
        field_type = field_schema.get("type")
        
        # Validate field based on type
        if field_type == "string":
            is_valid, error = validate_string(
                field_value,
                min_length=field_schema.get("min_length"),
                max_length=field_schema.get("max_length"),
                pattern=field_schema.get("pattern"),
            )
            if not is_valid:
                errors[field_name] = error
                
        elif field_type == "integer":
            is_valid, error = validate_integer(
                field_value,
                min_value=field_schema.get("min_value"),
                max_value=field_schema.get("max_value"),
            )
            if not is_valid:
                errors[field_name] = error
                
        elif field_type == "float":
            is_valid, error = validate_float(
                field_value,
                min_value=field_schema.get("min_value"),
                max_value=field_schema.get("max_value"),
            )
            if not is_valid:
                errors[field_name] = error
                
        elif field_type == "boolean":
            is_valid, error = validate_boolean(field_value)
            if not is_valid:
                errors[field_name] = error
                
        elif field_type == "date":
            is_valid, error = validate_date(
                field_value,
                format_str=field_schema.get("format", "%Y-%m-%d"),
                min_date=field_schema.get("min_date"),
                max_date=field_schema.get("max_date"),
            )
            if not is_valid:
                errors[field_name] = error
                
        elif field_type == "email":
            is_valid, error = validate_email(field_value)
            if not is_valid:
                errors[field_name] = error
                
        elif field_type == "url":
            is_valid, error = validate_url(
                field_value,
                required_schemes=field_schema.get("required_schemes"),
            )
            if not is_valid:
                errors[field_name] = error
                
        elif field_type == "ip_address":
            is_valid, error = validate_ip_address(field_value)
            if not is_valid:
                errors[field_name] = error
                
        elif field_type == "list":
            is_valid, error = validate_list(
                field_value,
                min_length=field_schema.get("min_length"),
                max_length=field_schema.get("max_length"),
            )
            if not is_valid:
                errors[field_name] = error
                
        elif field_type == "dict":
            is_valid, error = validate_dict(
                field_value,
                required_keys=field_schema.get("required_keys"),
                optional_keys=field_schema.get("optional_keys"),
                allow_extra_keys=field_schema.get("allow_extra_keys", False),
            )
            if not is_valid:
                errors[field_name] = error
        
        # Custom validation function
        custom_validator = field_schema.get("validator")
        if custom_validator and callable(custom_validator):
            is_valid, error = custom_validator(field_value)
            if not is_valid:
                errors[field_name] = error
    
    return len(errors) == 0, errors or None