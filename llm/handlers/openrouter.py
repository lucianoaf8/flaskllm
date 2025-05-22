# llm/handlers/openrouter.py
"""
OpenRouter Handler Module

This module implements the LLM handler for OpenRouter API,
which provides access to multiple AI models from different providers.
"""
from typing import Dict, Generator, List, Optional, Union, cast

import httpx
import json
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from core.exceptions import LLMAPIError
from core.logging import get_logger
from ..base_llm_handler import BaseLLMHandler

# Configure logger
logger = get_logger(__name__)

class OpenRouterHandler(BaseLLMHandler):
    """Handler for processing prompts with OpenRouter API."""

    def __init__(self, api_key: str, model: str = "openai/gpt-4o", timeout: int = 30):
        """
        Initialize OpenRouter handler.

        Args:
            api_key: OpenRouter API key
            model: Model to use (provider/model format)
            timeout: Request timeout in seconds
        """
        super().__init__(api_key, model, timeout)
        self.base_url = "https://openrouter.ai/api/v1"
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://flaskllm.example.com",  # Replace with your domain
                "X-Title": "FlaskLLM API"
            },
            timeout=timeout
        )

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(3),
    )
    def process_prompt(
        self,
        prompt: str,
        source: Optional[str] = None,
        language: Optional[str] = None,
        type: Optional[str] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[str, Generator[str, None, None]]:
        """
        Process a prompt using the OpenRouter API.

        Args:
            prompt: The prompt to process
            source: Source of the prompt (email, meeting, etc.)
            language: Target language code (ISO 639-1)
            type: Type of processing to perform
            stream: Whether to stream the response
            **kwargs: Additional parameters for the OpenRouter API

        Returns:
            Processed result as a string or a generator yielding chunks of the response

        Raises:
            LLMAPIError: If the OpenRouter API returns an error
        """
        try:
            # Create system prompt based on parameters
            system_prompt = self.create_system_prompt(source, language, type)

            # Prepare messages
            messages = []
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            messages.append({
                "role": "user",
                "content": prompt
            })

            # Log the request (without the full prompt for privacy)
            logger.info(
                "Sending request to OpenRouter",
                model=self.model,
                prompt_length=len(prompt),
                source=source,
                language=language,
                type=type,
                stream=stream
            )

            # Prepare request payload
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": stream,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 1024),
            }

            # Add other supported parameters
            for param in ["top_p", "frequency_penalty", "presence_penalty", "stop"]:
                if param in kwargs:
                    payload[param] = kwargs[param]

            if stream:
                # Return a generator for streaming
                return self._stream_response(payload)
            else:
                # For non-streaming, make a regular request
                response = self.client.post("/chat/completions", json=payload)
                response.raise_for_status()
                data = response.json()

                if "choices" not in data or not data["choices"] or "message" not in data["choices"][0]:
                    raise LLMAPIError("Invalid response from OpenRouter API")

                return data["choices"][0]["message"]["content"] or ""

        except httpx.HTTPStatusError as e:
            error_message = f"HTTP error from OpenRouter API: {e.response.status_code}"
            try:
                error_data = e.response.json()
                if "error" in error_data:
                    error_message = f"OpenRouter API error: {error_data['error']}"
            except Exception:
                pass

            logger.error(error_message, status_code=e.response.status_code)
            raise LLMAPIError(error_message)

        except httpx.RequestError as e:
            logger.error(f"Request error with OpenRouter API: {str(e)}")
            raise LLMAPIError(f"Request error with OpenRouter API: {str(e)}")

        except Exception as e:
            logger.exception(f"Unexpected error with OpenRouter API: {str(e)}")
            raise LLMAPIError(f"Unexpected error with OpenRouter API: {str(e)}")

    def _stream_response(self, payload: Dict) -> Generator[str, None, None]:
        """
        Stream response from OpenRouter API.

        Args:
            payload: Request payload

        Returns:
            Generator yielding chunks of the response

        Raises:
            LLMAPIError: If the OpenRouter API returns an error
        """
        try:
            with self.client.stream("POST", "/chat/completions", json=payload, timeout=120) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if not line.strip() or line.startswith(b"data: [DONE]"):
                        continue

                    if line.startswith(b"data: "):
                        line = line[6:]  # Remove "data: " prefix

                        # Skip comment payloads (OpenRouter sends these to keep connections alive)
                        if line.startswith(b": "):
                            continue

                        try:
                            data = json.loads(line)
                            if "choices" in data and data["choices"] and "delta" in data["choices"][0]:
                                delta = data["choices"][0]["delta"]
                                if "content" in delta and delta["content"]:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            # Skip invalid JSON
                            continue

        except httpx.HTTPStatusError as e:
            error_message = f"HTTP error from OpenRouter API during streaming: {e.response.status_code}"
            try:
                error_data = e.response.json()
                if "error" in error_data:
                    error_message = f"OpenRouter API streaming error: {error_data['error']}"
            except Exception:
                pass

            logger.error(error_message, status_code=e.response.status_code)
            raise LLMAPIError(error_message)

        except httpx.RequestError as e:
            logger.error(f"Request error with OpenRouter API during streaming: {str(e)}")
            raise LLMAPIError(f"Request error with OpenRouter API during streaming: {str(e)}")

        except Exception as e:
            logger.exception(f"Unexpected error with OpenRouter API during streaming: {str(e)}")
            raise LLMAPIError(f"Unexpected error with OpenRouter API during streaming: {str(e)}")
