# flaskllm/llm/factory.py
"""
LLM Factory Module

This module implements the factory pattern for creating LLM handlers
based on the configured provider.
"""
from typing import Protocol, runtime_checkable, Optional

from flaskllm.core.config import LLMProvider, Settings
from flaskllm.core.exceptions import LLMAPIError
from flaskllm.core.logging import get_logger

# Configure logger
logger = get_logger(__name__)


@runtime_checkable
class LLMHandler(Protocol):
    """Protocol defining the interface for LLM handlers."""

    def process_prompt(
        self,
        prompt: str,
        source: Optional[str] = None,
        language: Optional[str] = None,
        type: Optional[str] = None,
    ) -> str:
        """
        Process a prompt using the LLM.

        Args:
            prompt: The prompt to process
            source: Source of the prompt (email, meeting, etc.)
            language: Target language code (ISO 639-1)
            type: Type of processing to perform

        Returns:
            Processed result as a string
        """
        ...


def get_llm_handler(settings: Settings) -> LLMHandler:
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

    if provider == LLMProvider.OPENAI:
        from flaskllm.llm.openai_handler import OpenAIHandler

        if not settings.openai_api_key:
            raise LLMAPIError("OpenAI API key is not configured")

        logger.info("Initializing OpenAI handler", model=settings.openai_model)
        handler: LLMHandler = OpenAIHandler(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            timeout=settings.request_timeout,
        )
        return handler

    elif provider == LLMProvider.ANTHROPIC:
        from flaskllm.llm.anthropic_handler import AnthropicHandler

        if not settings.anthropic_api_key:
            raise LLMAPIError("Anthropic API key is not configured")

        logger.info("Initializing Anthropic handler", model=settings.anthropic_model)
        anthropic_handler: LLMHandler = AnthropicHandler(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
            timeout=settings.request_timeout,
        )
        return anthropic_handler

    else:
        raise LLMAPIError(f"Unsupported LLM provider: {provider}")
