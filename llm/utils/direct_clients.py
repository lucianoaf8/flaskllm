# llm/utils/direct_clients.py
"""
OpenAI Direct Client Module

This module provides a direct HTTP client for OpenAI's API without using
their client library, which can be useful to avoid client initialization issues
or versioning problems.
"""
import json
from typing import Any, Dict, List, Optional

import requests
from requests.exceptions import RequestException, Timeout
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from core.exceptions import LLMAPIError
from core.logging import get_logger

# Configure logger
logger = get_logger(__name__)

class OpenAIDirectClient:
    """Direct HTTP client for OpenAI's API."""

    # OpenAI API endpoints - should be configurable for testing or alternative endpoints
    BASE_URL = "https://api.openai.com/v1"
    CHAT_COMPLETIONS_URL = f"{BASE_URL}/chat/completions"

    def __init__(self, api_key: str, timeout: int = 30):
        """
        Initialize OpenAI direct client.

        Args:
            api_key: OpenAI API key
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = timeout
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        if not api_key:
            raise LLMAPIError("OpenAI API key is required")

        logger.info("Initialized OpenAI direct client")

    @retry(
        retry=retry_if_exception_type((RequestException, Timeout)),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(3),
    )
    def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4",
        temperature: float = 0.3,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Create a chat completion using the OpenAI API directly via HTTP.

        Args:
            messages: List of messages for the conversation
            model: Model to use
            temperature: Temperature parameter for response generation
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional parameters for the API call

        Returns:
            Response data as a dictionary

        Raises:
            LLMAPIError: If the OpenAI API returns an error
        """
        try:
            # Prepare request data
            data = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            # Add any additional parameters from kwargs
            for k, v in kwargs.items():
                if k not in ["model", "messages", "temperature", "max_tokens"]:
                    data[k] = v

            # Log the request (without the full messages for privacy)
            logger.info(
                "Sending direct request to OpenAI",
                model=model,
                messages_count=len(messages),
            )

            # Send the request
            response = requests.post(
                self.CHAT_COMPLETIONS_URL,
                headers=self.headers,
                json=data,
                timeout=self.timeout,
            )

            # Handle response status
            if response.status_code != 200:
                error_message = self._get_error_message(response)
                logger.error(
                    "OpenAI API error",
                    status_code=response.status_code,
                    error=error_message,
                )
                raise LLMAPIError(
                    f"OpenAI API error: {response.status_code} - {error_message}"
                )

            # Return the response data
            response_data = response.json()
            logger.info(
                "Received response from OpenAI",
                model=model,
                choices_count=len(response_data.get("choices", [])),
            )
            
            return response_data

        except Timeout:
            logger.error("Timeout while connecting to OpenAI API")
            raise LLMAPIError("Timeout while connecting to OpenAI API")

        except RequestException as e:
            logger.error(f"Error connecting to OpenAI API: {str(e)}")
            raise LLMAPIError(f"Error connecting to OpenAI API: {str(e)}")

        except Exception as e:
            logger.exception(f"Unexpected error with OpenAI API: {str(e)}")
            raise LLMAPIError(f"Unexpected error: {str(e)}")

    def _get_error_message(self, response: requests.Response) -> str:
        """
        Extract error message from OpenAI API response.

        Args:
            response: Response from OpenAI API

        Returns:
            Error message
        """
        try:
            error_data = response.json()
            if "error" in error_data:
                if isinstance(error_data["error"], dict) and "message" in error_data["error"]:
                    return error_data["error"]["message"]
                return str(error_data["error"])
            return response.text
        except Exception:
            return response.text
