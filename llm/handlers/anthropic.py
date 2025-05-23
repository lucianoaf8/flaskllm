# flaskllm/llm/handlers/anthropic.py
"""
Anthropic Handler Module

This module implements the LLM handler for Anthropic's Claude API using the BaseLLMHandler
interface for consistent behavior across handler implementations.
"""
from typing import Optional, Any, cast

# Handle different anthropic library versions
try:
    import anthropic
    from anthropic import Anthropic
    
    # Try to import the exceptions - they may have different names in different versions
    try:
        from anthropic import APIError, RateLimitError, AuthenticationError
    except ImportError:
        try:
            # Older versions might use different names
            from anthropic import APIError
            from anthropic import RateLimitError as AnthropicRateLimitError
            from anthropic import AuthenticationError as AnthropicAuthenticationError
            RateLimitError = AnthropicRateLimitError
            AuthenticationError = AnthropicAuthenticationError
        except ImportError:
            # Fallback for very old versions or missing exceptions
            APIError = Exception
            RateLimitError = Exception
            AuthenticationError = Exception
except ImportError:
    # If anthropic is not installed at all
    anthropic = None
    Anthropic = None
    APIError = Exception
    RateLimitError = Exception  
    AuthenticationError = Exception

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential
)

from api.v1.schemas.common import PromptSource, PromptType
from core.exceptions import LLMAPIError
from core.logging import get_logger
from ..base_llm_handler import BaseLLMHandler

# Configure logger
logger = get_logger(__name__)


class AnthropicHandler(BaseLLMHandler):
    """Handler for processing prompts with Anthropic's Claude API."""

    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229", timeout: int = 30):
        """
        Initialize Anthropic handler.

        Args:
            api_key: Anthropic API key
            model: Anthropic model to use
            timeout: Request timeout in seconds
        """
        super().__init__(api_key, model, timeout)
        
        if anthropic is None:
            raise LLMAPIError("Anthropic library is not installed. Please install it with: pip install anthropic")
            
        self.client = Anthropic(api_key=api_key, timeout=timeout)
        self.max_tokens_to_sample = 1024  # Adjust based on expected response length

    @retry(
        retry=retry_if_exception_type((Exception,)),  # Retry on any exception for now
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(3),
    )
    def process_prompt(
        self,
        prompt: str,
        source: Optional[str] = None,
        language: Optional[str] = None,
        type: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Process a prompt using the Anthropic API.

        Args:
            prompt: The prompt to process
            source: Source of the prompt (email, meeting, etc.)
            language: Target language code (ISO 639-1)
            type: Type of processing to perform
            **kwargs: Additional parameters for the API call

        Returns:
            Processed result as a string

        Raises:
            LLMAPIError: If the Anthropic API returns an error
        """
        try:
            # Create system prompt based on the parameters
            system_prompt = self.create_system_prompt(source, language, type)

            # Log the request (without the full prompt for privacy)
            logger.info(
                "Sending request to Anthropic",
                model=self.model,
                prompt_length=len(prompt),
                source=source,
                language=language,
                type=type,
            )

            # Extract API parameters from kwargs or use defaults
            max_tokens = kwargs.get("max_tokens", 1024)
            temperature = kwargs.get("temperature", 0.3)
            
            # Prepare message parameters
            message_params = {
                "model": self.model,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            
            # Add any additional parameters from kwargs
            for k, v in kwargs.items():
                if k not in ["max_tokens", "temperature"]:
                    message_params[k] = v

            # Send request to Anthropic
            response = self.client.messages.create(**message_params)

            # Extract and return the response content
            if not response.content or len(response.content) == 0:
                raise LLMAPIError("Empty response from Anthropic API")

            # Get the text content from the first content block
            content_block = response.content[0]
            if content_block.type != "text":
                raise LLMAPIError(
                    f"Unexpected content type from Anthropic API: {content_block.type}"
                )

            result = content_block.text
            logger.info(
                "Received response from Anthropic",
                model=self.model,
                response_length=len(result),
            )
            
            return result

        except Exception as e:
            # Check if it's one of the known Anthropic exceptions
            error_type = type(e).__name__
            error_message = str(e)
            
            if "authentication" in error_type.lower() or "auth" in error_message.lower():
                logger.error("Anthropic authentication error", error=error_message)
                raise LLMAPIError(f"Authentication error with Anthropic API: {error_message}")
            elif "rate" in error_type.lower() or "rate limit" in error_message.lower():
                logger.error("Anthropic rate limit exceeded", error=error_message)
                raise LLMAPIError(f"Rate limit exceeded with Anthropic API: {error_message}")
            elif "api" in error_type.lower():
                logger.error("Anthropic API error", error=error_message)
                raise LLMAPIError(f"Error from Anthropic API: {error_message}")
            else:
                logger.exception("Unexpected error with Anthropic API", error=error_message)
                raise LLMAPIError(f"Unexpected error: {error_message}")
