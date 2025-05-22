# flaskllm/llm/base_llm_handler.py
"""
Base LLM Handler Module

This module defines the abstract base class that all LLM handlers must implement.
It standardizes the interface for different LLM providers and ensures consistent
handling of prompts, errors, and responses.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import hashlib
import json

from api.v1.schemas import PromptSource, PromptType
from core.exceptions import LLMAPIError
from core.logging import get_logger
from core.config import Settings

# Configure logger
logger = get_logger(__name__)


class BaseLLMHandler(ABC):
    """Abstract base class for all LLM handlers."""

    def __init__(self, api_key: str, model: str, timeout: int = 30):
        """
        Initialize the LLM handler.

        Args:
            api_key: API key for the LLM provider
            model: Model identifier to use
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        logger.info(f"Initialized {self.__class__.__name__} with model {model}")

    @abstractmethod
    def process_prompt(
        self,
        prompt: str,
        source: Optional[str] = None,
        language: Optional[str] = None,
        type: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Process a prompt using the LLM provider.

        Args:
            prompt: The text prompt to process
            source: Source of the prompt (email, meeting, etc.)
            language: Target language code (ISO 639-1)
            type: Type of processing to perform
            **kwargs: Additional provider-specific parameters

        Returns:
            Processed result as a string

        Raises:
            LLMAPIError: If the API returns an error
        """
        pass

    def create_system_prompt(
        self,
        source: Optional[str] = None,
        language: Optional[str] = None,
        type: Optional[str] = None,
    ) -> str:
        """
        Create a system prompt based on the parameters.

        Args:
            source: Source of the prompt (email, meeting, etc.)
            language: Target language code (ISO 639-1)
            type: Type of processing to perform

        Returns:
            System prompt for the LLM provider
        """
        # Start with a base system prompt
        system_prompt = (
            "You are an AI assistant that helps process text content. "
            "Be concise, accurate, and helpful."
        )

        # Add source-specific instructions
        if source == PromptSource.EMAIL:
            system_prompt += (
                " The content is from an email. "
                "Focus on extracting the key information and action items."
            )
        elif source == PromptSource.MEETING:
            system_prompt += (
                " The content is from a meeting transcript. "
                "Focus on decisions, action items, and key discussion points."
            )
        elif source == PromptSource.DOCUMENT:
            system_prompt += (
                " The content is from a document. "
                "Focus on extracting the main themes and important details."
            )

        # Add type-specific instructions
        if type == PromptType.SUMMARY:
            system_prompt += (
                " Create a concise summary of the content, "
                "focusing on the most important information. "
                "Use bullet points for key points if appropriate."
            )
        elif type == PromptType.KEYWORDS:
            system_prompt += (
                " Extract the most important keywords and phrases from the content. "
                "Return them as a comma-separated list."
            )
        elif type == PromptType.SENTIMENT:
            system_prompt += (
                " Analyze the sentiment of the content. "
                "Consider the tone, emotion, and attitude expressed. "
                "Classify as positive, negative, or neutral, with a brief explanation."
            )
        elif type == PromptType.ENTITIES:
            system_prompt += (
                " Extract named entities from the content, such as people, organizations, "
                "locations, dates, and product names. Format as a structured list."
            )
        elif type == PromptType.TRANSLATION:
            target_lang = language or "English"
            system_prompt += (
                f" Translate the content into {target_lang}. "
                "Maintain the original meaning and tone as much as possible."
            )

        # Language-specific instructions (if not already covered by translation)
        if language and type != PromptType.TRANSLATION:
            system_prompt += f" Respond in {language}."

        return system_prompt


class CachedLLMHandler(BaseLLMHandler):
    """Decorator class that adds caching to any LLM handler."""

    def __init__(self, handler: BaseLLMHandler, settings: Settings):
        """
        Initialize the cached handler.

        Args:
            handler: The LLM handler to decorate with caching
            settings: Application settings for cache configuration
        """
        self.handler = handler
        self.settings = settings
        
        # Pass through properties from the wrapped handler
        self.api_key = handler.api_key
        self.model = handler.model
        self.timeout = handler.timeout
        
        # Initialize cache based on settings
        from core.cache import get_cache
        self.cache = get_cache(settings)
        logger.info(f"Initialized cached handler for {handler.__class__.__name__}")

    def process_prompt(
        self,
        prompt: str,
        source: Optional[str] = None,
        language: Optional[str] = None,
        type: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Process a prompt with caching support.

        Args:
            prompt: The text prompt to process
            source: Source of the prompt (email, meeting, etc.)
            language: Target language code (ISO 639-1)
            type: Type of processing to perform
            **kwargs: Additional provider-specific parameters

        Returns:
            Processed result as a string from cache or LLM

        Raises:
            LLMAPIError: If the API returns an error
        """
        # Create a cache key based on the prompt and parameters
        cache_key = self._create_cache_key(prompt, source, language, type, kwargs)
        
        # Try to get result from cache first
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.info("Retrieved result from cache", cache_key=cache_key)
            return cached_result
        
        # If not in cache, use the handler to process the prompt
        result = self.handler.process_prompt(prompt, source, language, type, **kwargs)
        
        # Cache the result for future use
        self.cache.set(
            cache_key, 
            result, 
            ttl=self.settings.cache_ttl_seconds
        )
        logger.info("Cached result for future use", cache_key=cache_key)
        
        return result

    def _create_cache_key(self, prompt: str, source: Optional[str], 
                          language: Optional[str], type: Optional[str],
                          kwargs: Dict[str, Any]) -> str:
        """
        Create a cache key based on the prompt and parameters.

        Args:
            prompt: The text prompt to process
            source: Source of the prompt
            language: Target language code
            type: Type of processing
            kwargs: Additional parameters

        Returns:
            Cache key as a string
        """
        import hashlib
        # Create a representation of the request for caching
        # Use a hash of the prompt to avoid very long keys
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        key_parts = [
            f"model:{self.handler.model}",
            f"prompt:{prompt_hash}",
            f"source:{source or 'none'}",
            f"language:{language or 'none'}",
            f"type:{type or 'none'}",
        ]
        
        # Add any extra kwargs to the cache key
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
            
        return "llm:" + ":".join(key_parts)
