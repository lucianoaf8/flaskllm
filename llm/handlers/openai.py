# flaskllm/llm/handlers/openai.py
"""
OpenAI Handler Module

This module implements the LLM handler for OpenAI's API using the BaseLLMHandler
interface for consistent behavior across handler implementations.

Version History:
- Consolidated from:
  - openai_handler.py: Original implementation
  - openai_handler_v2.py: Enhanced implementation with improved error handling
  - openai_direct.py: Direct HTTP handler implementation (handler portions only)
"""
from typing import Optional, Dict, List, Any
import openai
from openai import OpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

# Remove the circular import at module level
from core.exceptions import LLMAPIError
from core.logging import get_logger
from ..base_llm_handler import BaseLLMHandler

# Configure logger
logger = get_logger(__name__)


class OpenAIHandler(BaseLLMHandler):
    """Handler for processing prompts with OpenAI's API."""

    def __init__(self, api_key: str, model: str = "gpt-4o", timeout: int = 30):
        """
        Initialize OpenAI handler.

        Args:
            api_key: OpenAI API key
            model: OpenAI model to use
            timeout: Request timeout in seconds
        """
        super().__init__(api_key, model, timeout)

        # Initialize OpenAI client with better error handling
        try:
            self.client = OpenAI(
                api_key=api_key,
                timeout=timeout,
                max_retries=0,  # We'll handle retries ourselves with tenacity
            )
            logger.info(f"OpenAI client initialized successfully with model {model}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            raise LLMAPIError(f"Failed to initialize OpenAI client: {str(e)}")

    @retry(
        # Use the proper exception types for OpenAI v1.x
        retry=retry_if_exception_type(
            (
                openai.APIError,
                openai.APIConnectionError,
                openai.RateLimitError,
                openai.APITimeoutError,
            )
        ),
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
        Process a prompt using the OpenAI API.

        Args:
            prompt: The prompt to process
            source: Source of the prompt (email, meeting, etc.)
            language: Target language code (ISO 639-1)
            type: Type of processing to perform
            **kwargs: Additional parameters for the API call

        Returns:
            Processed result as a string

        Raises:
            LLMAPIError: If the OpenAI API returns an error
        """
        try:
            # Create messages based on the prompt and parameters
            messages = self._create_messages(prompt, source, language, type)

            # Log the request (without the full prompt for privacy)
            logger.info(
                "Sending request to OpenAI",
                model=self.model,
                prompt_length=len(prompt),
                source=source,
                language=language,
                type=type,
            )

            # Extract API parameters from kwargs or use defaults
            temperature = kwargs.get("temperature", 0.3)
            max_tokens = kwargs.get("max_tokens", 1024)
            
            # Send request to OpenAI with proper error handling
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **{k: v for k, v in kwargs.items() 
                   if k not in ["temperature", "max_tokens"]}
            )

            # Extract and return the response content with proper null checking
            if not response.choices or len(response.choices) == 0:
                logger.error("Empty response from OpenAI API")
                raise LLMAPIError("Empty response from OpenAI API")

            message = response.choices[0].message
            if not message or not message.content:
                logger.error("Empty message content from OpenAI API")
                raise LLMAPIError("Empty message content from OpenAI API")

            logger.info(
                "Successfully received response from OpenAI API",
                response_length=len(message.content)
            )
            return message.content

        except openai.AuthenticationError as e:
            logger.error(f"OpenAI authentication error: {str(e)}")
            raise LLMAPIError(f"Authentication error with OpenAI API: {str(e)}")

        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {str(e)}")
            raise LLMAPIError(f"Rate limit exceeded with OpenAI API: {str(e)}")

        except openai.BadRequestError as e:
            logger.error(f"Bad request to OpenAI API: {str(e)}")
            raise LLMAPIError(f"Bad request to OpenAI API: {str(e)}")

        except openai.APIConnectionError as e:
            logger.error(f"Connection error with OpenAI API: {str(e)}")
            raise LLMAPIError(f"Connection error with OpenAI API: {str(e)}")

        except openai.APITimeoutError as e:
            logger.error(f"Timeout error with OpenAI API: {str(e)}")
            raise LLMAPIError(f"Timeout error with OpenAI API: {str(e)}")

        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise LLMAPIError(f"Error from OpenAI API: {str(e)}")

        except Exception as e:
            logger.exception(f"Unexpected error with OpenAI API: {str(e)}")
            raise LLMAPIError(f"Unexpected error: {str(e)}")

    def _create_messages(
        self,
        prompt: str,
        source: Optional[str] = None,
        language: Optional[str] = None,
        type: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Create messages for the OpenAI API based on the parameters.

        Args:
            prompt: The prompt to process
            source: Source of the prompt (email, meeting, etc.)
            language: Target language code (ISO 639-1)
            type: Type of processing to perform

        Returns:
            List of message dictionaries for the OpenAI API
        """
        # Start with a system message that guides the model's behavior
        messages: List[Dict[str, str]] = [
            {
                "role": "system",
                "content": self.create_system_prompt(source, language, type),
            }
        ]

        # Add the user prompt
        messages.append({"role": "user", "content": prompt})

        return messages
