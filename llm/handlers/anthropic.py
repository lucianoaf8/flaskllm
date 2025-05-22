# flaskllm/llm/handlers/anthropic.py
"""
Anthropic Handler Module

This module implements the LLM handler for Anthropic's Claude API using the BaseLLMHandler
interface for consistent behavior across handler implementations.
"""
from typing import Optional, Any, cast
import anthropic
from anthropic import Anthropic
# Import exceptions - names may vary based on anthropic version
from anthropic import APIError, RateLimitError, AuthenticationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential
)

from api.v1.schemas import PromptSource, PromptType
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
        self.client = Anthropic(api_key=api_key, timeout=timeout)
        self.max_tokens_to_sample = 1024  # Adjust based on expected response length

    @retry(
        retry=retry_if_exception_type((APIError, RateLimitError)),
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

        except anthropic.AuthenticationError as e:
            logger.error("Anthropic authentication error", error=str(e))
            raise LLMAPIError(f"Authentication error with Anthropic API: {str(e)}")

        except RateLimitError as e:
            logger.error("Anthropic rate limit exceeded", error=str(e))
            raise LLMAPIError(f"Rate limit exceeded with Anthropic API: {str(e)}")

        except APIError as e:
            logger.error("Anthropic API error", error=str(e))
            raise LLMAPIError(f"Error from Anthropic API: {str(e)}")

        except Exception as e:
            logger.exception("Unexpected error with Anthropic API", error=str(e))
            raise LLMAPIError(f"Unexpected error: {str(e)}")
