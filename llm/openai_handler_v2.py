# flaskllm/llm/openai_handler_v2.py
"""
OpenAI Handler Module V2

This module implements a more robust LLM handler for OpenAI's API with comprehensive
error handling for v1.x of the OpenAI Python library.
"""
from typing import Dict, List, Optional, Any

import openai
from openai import OpenAI
from openai.types.chat import ChatCompletion
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


class OpenAIHandlerV2:
    """Improved handler for processing prompts with OpenAI's API."""

    def __init__(self, api_key: str, model: str = "gpt-4o", timeout: int = 30):
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
                extra={
                    "model": self.model,
                    "prompt_length": len(prompt),
                    "source": source,
                    "language": language,
                    "type": type,
                }
            )

            # Send request to OpenAI with proper error handling
            response: ChatCompletion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,  # Lower temperature for more focused responses
                max_tokens=1024,  # Adjust based on expected response length
            )

            # Extract and return the response content with proper null checking
            if not response.choices or len(response.choices) == 0:
                logger.error("Empty response from OpenAI API")
                raise LLMAPIError("Empty response from OpenAI API")
            
            message = response.choices[0].message
            if not message or not message.content:
                logger.error("Empty message content from OpenAI API")
                raise LLMAPIError("Empty message content from OpenAI API")
            
            logger.info("Successfully received response from OpenAI API")
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