# flaskllm/core/constants.py
"""
Application constants for the Flask LLM API.

This module defines constants used throughout the application to ensure
consistency and avoid magic values in the codebase.
"""

# API Response Constants
DEFAULT_SUCCESS_MESSAGE = "Request processed successfully"
DEFAULT_ERROR_MESSAGE = "An error occurred while processing your request"

# HTTP Status Codes (commonly used ones)
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_400_BAD_REQUEST = 400
HTTP_401_UNAUTHORIZED = 401
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_422_UNPROCESSABLE_ENTITY = 422
HTTP_429_TOO_MANY_REQUESTS = 429
HTTP_500_INTERNAL_SERVER_ERROR = 500

# Rate Limiting Constants
DEFAULT_RATE_LIMIT = 60  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_HEADER = "X-RateLimit-Limit"
RATE_LIMIT_REMAINING_HEADER = "X-RateLimit-Remaining"
RATE_LIMIT_RESET_HEADER = "X-RateLimit-Reset"

# API Headers
API_TOKEN_HEADER = "X-API-Token"
CONTENT_TYPE_HEADER = "Content-Type"
JSON_CONTENT_TYPE = "application/json"

# LLM Request Constants
DEFAULT_REQUEST_TIMEOUT = 30  # seconds
MAX_PROMPT_LENGTH = 4000
DEFAULT_TEMPERATURE = 0.7

# Cache Constants
DEFAULT_CACHE_EXPIRATION = 86400  # 24 hours in seconds
DEFAULT_CACHE_MAX_SIZE = 10000  # Maximum items to store

# File Size Limits
DEFAULT_MAX_FILE_SIZE_MB = 10
BYTES_PER_MB = 1048576  # 1024 * 1024
