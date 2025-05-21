# flaskllm/llm/factory.py
"""
LLM Factory Module

This module implements the factory pattern for creating LLM handlers
based on the configured provider.
"""
from typing import Optional, Protocol, runtime_checkable

from core.config import LLMProvider, Settings
from core.exceptions import LLMAPIError
from core.logging import get_logger

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
        try:
            # Try using the Direct handler first - this avoids all client initialization issues
            from llm.openai_direct import OpenAIDirectHandler

            if not settings.openai_api_key:
                raise LLMAPIError("OpenAI API key is not configured")

            logger.info(
                "Initializing OpenAI Direct handler", model=settings.openai_model
            )
            handler: LLMHandler = OpenAIDirectHandler(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                timeout=settings.request_timeout,
            )
            return handler
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI Direct handler: {str(e)}")

            try:
                # Fall back to V2 handler
                from llm.openai_handler_v2 import OpenAIHandlerV2

                if not settings.openai_api_key:
                    raise LLMAPIError("OpenAI API key is not configured")

                logger.info(
                    "Initializing OpenAI handler V2", model=settings.openai_model
                )
                handler: LLMHandler = OpenAIHandlerV2(
                    api_key=settings.openai_api_key,
                    model=settings.openai_model,
                    timeout=settings.request_timeout,
                )
                return handler
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI V2 handler: {str(e)}")

                # Fall back to the standard handler
                from llm.openai_handler import OpenAIHandler

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
        from llm.anthropic_handler import AnthropicHandler

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
