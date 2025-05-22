# flaskllm/llm/factory.py
"""
LLM Factory Module

This module implements the factory pattern for creating LLM handlers
based on the configured provider. It provides a centralized way to
instantiate the appropriate LLM handler based on application settings.
"""
from typing import Optional, Type, Dict, Any

from core.config import LLMProvider, Settings
from core.exceptions import LLMAPIError
from core.logging import get_logger

from .base_llm_handler import BaseLLMHandler, CachedLLMHandler

# Configure logger
logger = get_logger(__name__)


# Handler mapping for different provider types
_HANDLER_MAPPING: Dict[LLMProvider, Dict[str, Type[BaseLLMHandler]]] = {}


def register_handler(provider: LLMProvider, handler_type: str, handler_class: Type[BaseLLMHandler]) -> None:
    """
    Register a handler class for a specific provider and type.
    
    Args:
        provider: LLM provider enum value
        handler_type: Type of handler (e.g., 'standard', 'direct')
        handler_class: Handler class to register
    """
    if provider not in _HANDLER_MAPPING:
        _HANDLER_MAPPING[provider] = {}
    _HANDLER_MAPPING[provider][handler_type] = handler_class
    logger.debug(f"Registered {handler_class.__name__} for {provider} ({handler_type})")


# Import handlers and register them
from .openai_handler import OpenAIHandler
from .openai_handler_v2 import OpenAIHandlerV2
from .openai_direct import OpenAIDirectHandler
from .anthropic_handler import AnthropicHandler

# Register OpenAI handlers
register_handler(LLMProvider.OPENAI, "standard", OpenAIHandler)
register_handler(LLMProvider.OPENAI, "v2", OpenAIHandlerV2)
register_handler(LLMProvider.OPENAI, "direct", OpenAIDirectHandler)

# Register Anthropic handlers
register_handler(LLMProvider.ANTHROPIC, "standard", AnthropicHandler)


def get_llm_handler(settings: Settings) -> BaseLLMHandler:
    """
    Get an LLM handler based on the configured provider.

    Args:
        settings: Application settings

    Returns:
        LLM handler instance

    Raises:
        LLMAPIError: If the provider is not supported or configuration is invalid
    """
    provider = settings.llm_provider
    
    # Validate provider configuration
    _validate_provider_config(provider, settings)
    
    # Get the handler based on the provider
    if provider == LLMProvider.OPENAI:
        handler = _get_openai_handler(settings)
    elif provider == LLMProvider.ANTHROPIC:
        handler = _get_anthropic_handler(settings)
    else:
        raise LLMAPIError(f"Unsupported LLM provider: {provider}")
    
    # Apply caching if enabled
    if settings.cache_enabled:
        logger.info("Applying caching to the LLM handler")
        handler = CachedLLMHandler(handler, settings)
    
    return handler


def _validate_provider_config(provider: LLMProvider, settings: Settings) -> None:
    """
    Validate provider configuration in settings.
    
    Args:
        provider: LLM provider to validate
        settings: Application settings
        
    Raises:
        LLMAPIError: If the configuration is invalid
    """
    if provider == LLMProvider.OPENAI and not settings.openai_api_key:
        raise LLMAPIError("OpenAI API key is not configured")
    elif provider == LLMProvider.ANTHROPIC and not settings.anthropic_api_key:
        raise LLMAPIError("Anthropic API key is not configured")


def _get_openai_handler(settings: Settings) -> BaseLLMHandler:
    """
    Get an OpenAI handler with fallback logic.
    
    Args:
        settings: Application settings
        
    Returns:
        OpenAI handler instance
        
    Raises:
        LLMAPIError: If all handler initialization attempts fail
    """
    # List of handler types to try in order of preference
    handler_types = ["direct", "v2", "standard"]
    exceptions = []
    
    for handler_type in handler_types:
        try:
            handler_class = _HANDLER_MAPPING[LLMProvider.OPENAI][handler_type]
            logger.info(
                f"Initializing {handler_class.__name__}", 
                model=settings.openai_model
            )
            
            handler = handler_class(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                timeout=settings.request_timeout,
            )
            return handler
        except Exception as e:
            logger.warning(
                f"Failed to initialize {handler_type} OpenAI handler", 
                error=str(e)
            )
            exceptions.append((handler_type, str(e)))
    
    # If all handler initialization attempts failed, raise an error
    error_details = "; ".join([f"{t}: {e}" for t, e in exceptions])
    raise LLMAPIError(f"Failed to initialize any OpenAI handler: {error_details}")


def _get_anthropic_handler(settings: Settings) -> BaseLLMHandler:
    """
    Get an Anthropic handler.
    
    Args:
        settings: Application settings
        
    Returns:
        Anthropic handler instance
    """
    handler_class = _HANDLER_MAPPING[LLMProvider.ANTHROPIC]["standard"]
    logger.info(
        f"Initializing {handler_class.__name__}", 
        model=settings.anthropic_model
    )
    
    return handler_class(
        api_key=settings.anthropic_api_key,
        model=settings.anthropic_model,
        timeout=settings.request_timeout,
    )
