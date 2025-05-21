# flaskllm/llm/openai_handler.py
"""
OpenAI Handler Module

This module implements the LLM handler for OpenAI's API.
"""
from typing import Dict, List, Optional

import openai
from openai import OpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from flaskllm.api.v1.schemas import PromptSource, PromptType
from flaskllm.core.exceptions import LLMAPIError
from flaskllm.core.logging import get_logger

# Configure logger
logger = get_logger(__name__)


class OpenAIHandler:
    """Handler for processing prompts with OpenAI's API."""

    def __init__(self, api_key: str, model: str = "gpt-4", timeout: int = 30):
        """
        Initialize OpenAI handler.

        Args:
            api_key: OpenAI API key
            model: OpenAI model to use
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.client = OpenAI(api_key=api_key, timeout=timeout)

    @retry(
        retry=retry_if_exception_type(
            (openai.APIError, openai.APIConnectionError, openai.RateLimitError)
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
    ) -> str:
        """
        Process a prompt using the OpenAI API.

        Args:
            prompt: The prompt to process
            source: Source of the prompt (email, meeting, etc.)
            language: Target language code (ISO 639-1)
            type: Type of processing to perform

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

            # Send request to OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,  # Lower temperature for more focused responses
                max_tokens=1024,  # Adjust based on expected response length
            )

            # Extract and return the response content
            if not response.choices or not response.choices[0].message:
                raise LLMAPIError("Empty response from OpenAI API")

            return response.choices[0].message.content or ""

        except openai.AuthenticationError as e:
            logger.error("OpenAI authentication error", error=str(e))
            raise LLMAPIError("Authentication error with OpenAI API")

        except openai.RateLimitError as e:
            logger.error("OpenAI rate limit exceeded", error=str(e))
            raise LLMAPIError("Rate limit exceeded with OpenAI API")

        except openai.APIError as e:
            logger.error("OpenAI API error", error=str(e))
            raise LLMAPIError(f"Error from OpenAI API: {str(e)}")

        except Exception as e:
            logger.exception("Unexpected error with OpenAI API", error=str(e))
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
                "content": self._create_system_prompt(source, language, type),
            }
        ]

        # Add the user prompt
        messages.append({"role": "user", "content": prompt})

        return messages

    def _create_system_prompt(
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
            System prompt for the OpenAI API
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
