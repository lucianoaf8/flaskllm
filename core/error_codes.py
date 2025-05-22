# flaskllm/core/error_codes.py
"""
Error code definitions for the Flask LLM API.

This module defines error codes, messages, and associated HTTP status codes
to ensure consistent error reporting throughout the application.
"""

from enum import Enum
from typing import Dict, Any

from core.constants import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_500_INTERNAL_SERVER_ERROR,
)


class ErrorCode(str, Enum):
    """Error codes for the Flask LLM API."""
    
    # Authentication errors (1000-1999)
    INVALID_TOKEN = "AUTH_1001"
    MISSING_TOKEN = "AUTH_1002"
    EXPIRED_TOKEN = "AUTH_1003"
    INSUFFICIENT_PERMISSIONS = "AUTH_1004"
    
    # Validation errors (2000-2999)
    INVALID_REQUEST_FORMAT = "VAL_2001"
    MISSING_REQUIRED_FIELD = "VAL_2002"
    INVALID_FIELD_VALUE = "VAL_2003"
    PROMPT_TOO_LONG = "VAL_2004"
    
    # Rate limiting errors (3000-3999)
    RATE_LIMIT_EXCEEDED = "RATE_3001"
    
    # LLM provider errors (4000-4999)
    LLM_API_ERROR = "LLM_4001"
    PROVIDER_TIMEOUT = "LLM_4002"
    PROVIDER_UNAVAILABLE = "LLM_4003"
    MODEL_NOT_AVAILABLE = "LLM_4004"
    CONTENT_FILTERED = "LLM_4005"
    
    # Cache errors (5000-5999)
    CACHE_UNAVAILABLE = "CACHE_5001"
    
    # Resource errors (6000-6999)
    RESOURCE_NOT_FOUND = "RES_6001"
    
    # Server errors (9000-9999)
    INTERNAL_SERVER_ERROR = "SRV_9001"
    CONFIGURATION_ERROR = "SRV_9002"
    DEPENDENCY_ERROR = "SRV_9003"


# Error details mapping
ERROR_DETAILS: Dict[ErrorCode, Dict[str, Any]] = {
    # Authentication errors
    ErrorCode.INVALID_TOKEN: {
        "message": "Invalid API token provided",
        "status_code": HTTP_401_UNAUTHORIZED,
    },
    ErrorCode.MISSING_TOKEN: {
        "message": "API token is required",
        "status_code": HTTP_401_UNAUTHORIZED,
    },
    ErrorCode.EXPIRED_TOKEN: {
        "message": "API token has expired",
        "status_code": HTTP_401_UNAUTHORIZED,
    },
    ErrorCode.INSUFFICIENT_PERMISSIONS: {
        "message": "Insufficient permissions for this operation",
        "status_code": HTTP_403_FORBIDDEN,
    },
    
    # Validation errors
    ErrorCode.INVALID_REQUEST_FORMAT: {
        "message": "Invalid request format",
        "status_code": HTTP_400_BAD_REQUEST,
    },
    ErrorCode.MISSING_REQUIRED_FIELD: {
        "message": "Required field is missing",
        "status_code": HTTP_400_BAD_REQUEST,
    },
    ErrorCode.INVALID_FIELD_VALUE: {
        "message": "Field contains an invalid value",
        "status_code": HTTP_400_BAD_REQUEST,
    },
    ErrorCode.PROMPT_TOO_LONG: {
        "message": "Prompt exceeds maximum allowed length",
        "status_code": HTTP_400_BAD_REQUEST,
    },
    
    # Rate limiting errors
    ErrorCode.RATE_LIMIT_EXCEEDED: {
        "message": "Rate limit exceeded",
        "status_code": HTTP_429_TOO_MANY_REQUESTS,
    },
    
    # LLM provider errors
    ErrorCode.LLM_API_ERROR: {
        "message": "Error from LLM provider API",
        "status_code": HTTP_500_INTERNAL_SERVER_ERROR,
    },
    ErrorCode.PROVIDER_TIMEOUT: {
        "message": "LLM provider request timed out",
        "status_code": HTTP_500_INTERNAL_SERVER_ERROR,
    },
    ErrorCode.PROVIDER_UNAVAILABLE: {
        "message": "LLM provider service is unavailable",
        "status_code": HTTP_500_INTERNAL_SERVER_ERROR,
    },
    ErrorCode.MODEL_NOT_AVAILABLE: {
        "message": "Requested LLM model is not available",
        "status_code": HTTP_400_BAD_REQUEST,
    },
    ErrorCode.CONTENT_FILTERED: {
        "message": "Content was filtered by LLM provider safety systems",
        "status_code": HTTP_422_UNPROCESSABLE_ENTITY,
    },
    
    # Cache errors
    ErrorCode.CACHE_UNAVAILABLE: {
        "message": "Cache service is unavailable",
        "status_code": HTTP_500_INTERNAL_SERVER_ERROR,
    },
    
    # Resource errors
    ErrorCode.RESOURCE_NOT_FOUND: {
        "message": "Requested resource not found",
        "status_code": HTTP_404_NOT_FOUND,
    },
    
    # Server errors
    ErrorCode.INTERNAL_SERVER_ERROR: {
        "message": "Internal server error",
        "status_code": HTTP_500_INTERNAL_SERVER_ERROR,
    },
    ErrorCode.CONFIGURATION_ERROR: {
        "message": "Server configuration error",
        "status_code": HTTP_500_INTERNAL_SERVER_ERROR,
    },
    ErrorCode.DEPENDENCY_ERROR: {
        "message": "Error in external dependency",
        "status_code": HTTP_500_INTERNAL_SERVER_ERROR,
    },
}


def get_error_details(code: ErrorCode, custom_message: str = None) -> Dict[str, Any]:
    """Get error details for an error code with optional custom message.
    
    Args:
        code: The error code
        custom_message: Optional custom message to override the default
        
    Returns:
        Dictionary with error details including code, message, and status code
    """
    details = ERROR_DETAILS[code].copy()
    if custom_message:
        details["message"] = custom_message
    details["code"] = code
    return details
