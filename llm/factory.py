# flaskllm/llm/factory.py
"""
LLM Factory Module

This module implements the factory pattern for creating LLM handlers
based on the configured provider. It provides a centralized way to
instantiate the appropriate LLM handler based on application settings.
"""
from typing import Protocol, runtime_checkable, Optional, Type, Dict, Any

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
from .handlers.openai import OpenAIHandler
from .utils.direct_clients import OpenAIDirectClient
from .handlers.anthropic import AnthropicHandler
from .handlers.openrouter import OpenRouterHandler

# Register OpenAI handlers
register_handler(LLMProvider.OPENAI, "standard", OpenAIHandler)

# Register Anthropic handlers
register_handler(LLMProvider.ANTHROPIC, "standard", AnthropicHandler)

# Register OpenRouter handlers
register_handler(LLMProvider.OPEN_ROUTINE, "standard", OpenRouterHandler)


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
    elif provider == LLMProvider.OPEN_ROUTINE:
        handler = _get_openrouter_handler(settings)
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
    elif provider == LLMProvider.OPEN_ROUTINE and not settings.openrouter_api_key:
        raise LLMAPIError("OpenRouter API key is not configured")


def _get_openai_handler(settings: Settings) -> BaseLLMHandler:
    """
    Get an OpenAI handler.
    
    Args:
        settings: Application settings
        
    Returns:
        OpenAI handler instance
        
    Raises:
        LLMAPIError: If handler initialization fails
    """
    try:
        handler_class = _HANDLER_MAPPING[LLMProvider.OPENAI]["standard"]
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
        logger.error(
            "Failed to initialize OpenAI handler", 
            error=str(e)
        )
        raise LLMAPIError(f"Failed to initialize OpenAI handler: {str(e)}")


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


def _get_openrouter_handler(settings: Settings) -> BaseLLMHandler:
    """
    Get an OpenRouter handler.
    
    Args:
        settings: Application settings
        
    Returns:
        OpenRouter handler instance
    """
    handler_class = _HANDLER_MAPPING[LLMProvider.OPEN_ROUTINE]["standard"]
    logger.info(
        f"Initializing {handler_class.__name__}", 
        model=settings.openrouter_model
    )
    
    return handler_class(
        api_key=settings.openrouter_api_key,
        model=settings.openrouter_model,
        timeout=settings.request_timeout,
    )
