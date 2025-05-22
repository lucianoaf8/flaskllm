# core/error_codes.py
# Compatibility module to maintain backward compatibility with old imports
# This imports from the new location to avoid breaking existing code

from core.errors.codes import ErrorCode, ErrorCodes

# Re-export all symbols to maintain API compatibility
__all__ = ['ErrorCode', 'ErrorCodes']
