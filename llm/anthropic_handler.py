# flaskllm/llm/anthropic_handler.py
"""
Anthropic Handler Module

This module implements the LLM handler for Anthropic's Claude API.
"""
from typing import Optional, cast

import anthropic
from anthropic import Anthropic
from anthropic.types import ContentBlock
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from api.v1.schemas import PromptSource, PromptType
from core.exceptions import LLMAPIError
from core.logging import get_logger

# Configure logger
logger = get_logger(__name__)


class AnthropicHandler:
    """Handler for processing prompts with Anthropic's Claude API."""

    def __init__(self, api_key: str, model: str = "claude-2", timeout: int = 30):
        """
        Initialize Anthropic handler.

        Args:
            api_key: Anthropic API key
            model: Anthropic model to use
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.client = Anthropic(api_key=api_key, timeout=timeout)
        self.max_tokens_to_sample = 1024  # Adjust based on expected response length

    @retry(
        retry=retry_if_exception_type(anthropic.APIError),
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
        Process a prompt using the Anthropic API.

        Args:
            prompt: The prompt to process
            source: Source of the prompt (email, meeting, etc.)
            language: Target language code (ISO 639-1)
            type: Type of processing to perform

        Returns:
            Processed result as a string

        Raises:
            LLMAPIError: If the Anthropic API returns an error
        """
        try:
            # Create system prompt and user prompt
            system_prompt = self._create_system_prompt(source, language, type)

            # Log the request (without the full prompt for privacy)
            logger.info(
                "Sending request to Anthropic",
                model=self.model,
                prompt_length=len(prompt),
                source=source,
                language=language,
                type=type,
            )

            # Send request to Anthropic
            response = self.client.messages.create(
                model=self.model,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens_to_sample,
                temperature=0.3,  # Lower temperature for more focused responses
            )

            # Extract and return the response content
            if not response.content:
                raise LLMAPIError("Empty response from Anthropic API")
            
            # Get the first content block
            content_block = response.content[0]
            
            # Check if it's a text block and has text content
            if content_block.type != "text" or not content_block.text:
                raise LLMAPIError("Invalid or empty response from Anthropic API")
                
            # Text is now guaranteed to be a string
            result = cast(str, content_block.text)
            return result

        except anthropic.AuthenticationError as e:
            logger.error("Anthropic authentication error", error=str(e))
            raise LLMAPIError("Authentication error with Anthropic API")

        except anthropic.RateLimitError as e:
            logger.error("Anthropic rate limit exceeded", error=str(e))
            raise LLMAPIError("Rate limit exceeded with Anthropic API")

        except anthropic.APIError as e:
            logger.error("Anthropic API error", error=str(e))
            raise LLMAPIError(f"Error from Anthropic API: {str(e)}")

        except Exception as e:
            logger.exception("Unexpected error with Anthropic API", error=str(e))
            raise LLMAPIError(f"Unexpected error: {str(e)}")

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
            System prompt for the Anthropic API
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
