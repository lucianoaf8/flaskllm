#!/usr/bin/env python3
"""
OpenAI Direct Handler Module

This module implements a direct HTTP handler for OpenAI's API without using
their client library, which can be useful to avoid client initialization issues
or versioning problems. It uses the BaseLLMHandler interface for consistent behavior
across handler implementations.
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

from api.v1.schemas import PromptSource, PromptType
from core.exceptions import LLMAPIError
from core.logging import get_logger
from .base_llm_handler import BaseLLMHandler

# Configure logger
logger = get_logger(__name__)


class OpenAIDirectHandler(BaseLLMHandler):
    """Direct HTTP handler for OpenAI's API."""

    # OpenAI API endpoints - should be configurable for testing or alternative endpoints
    BASE_URL = "https://api.openai.com/v1"
    CHAT_COMPLETIONS_URL = f"{BASE_URL}/chat/completions"

    def __init__(self, api_key: str, model: str = "gpt-4", timeout: int = 30):
        """
        Initialize OpenAI direct handler.

        Args:
            api_key: OpenAI API key
            model: OpenAI model to use
            timeout: Request timeout in seconds
        """
        super().__init__(api_key, model, timeout)
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        if not api_key:
            raise LLMAPIError("OpenAI API key is required")

        logger.info(f"Initialized OpenAI direct handler with model {model}")

    @retry(
        retry=retry_if_exception_type((RequestException, Timeout)),
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
        Process a prompt using the OpenAI API directly via HTTP.

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

            # Extract API parameters from kwargs or use defaults
            temperature = kwargs.get("temperature", 0.3)
            max_tokens = kwargs.get("max_tokens", 1024)
            
            # Prepare request data
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            # Add any additional parameters from kwargs
            for k, v in kwargs.items():
                if k not in ["temperature", "max_tokens"]:
                    data[k] = v

            # Log the request (without the full prompt for privacy)
            logger.info(
                "Sending direct request to OpenAI",
                model=self.model,
                prompt_length=len(prompt),
                source=source,
                language=language,
                type=type,
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

            # Extract and return the response content
            response_data = response.json()
            if (
                not response_data.get("choices")
                or len(response_data["choices"]) == 0
                or not response_data["choices"][0].get("message")
                or not response_data["choices"][0]["message"].get("content")
            ):
                logger.error("Empty response from OpenAI API")
                raise LLMAPIError("Empty response from OpenAI API")

            result = response_data["choices"][0]["message"]["content"]
            logger.info(
                "Received response from OpenAI",
                model=self.model,
                response_length=len(result),
            )
            
            return result

        except Timeout:
            logger.error("Timeout while connecting to OpenAI API")
            raise LLMAPIError("Timeout while connecting to OpenAI API")

        except RequestException as e:
            logger.error(f"Error connecting to OpenAI API: {str(e)}")
            raise LLMAPIError(f"Error connecting to OpenAI API: {str(e)}")

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

    def create_system_prompt(
        self,
        source: Optional[str] = None,
        language: Optional[str] = None,
        type: Optional[str] = None,
    ) -> str:
        """Create a system prompt based on the parameters."""
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
                + "locations, dates, and product names. "  # noqa: E501
                + "Format as a structured list."
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
