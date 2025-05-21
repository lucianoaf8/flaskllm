#!/usr/bin/env python3
"""
OpenAI Direct Handler

This module implements a direct OpenAI API handler without using the client
initialization that causes the proxies error.
"""
from typing import Dict, List, Optional, Any
import os
import json
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from api.v1.schemas import PromptSource, PromptType
from core.exceptions import LLMAPIError
from core.logging import get_logger

# Configure logger
logger = get_logger(__name__)

class OpenAIDirectHandler:
    """
    Direct handler for OpenAI API without using their client library initialization.
    Avoids the 'proxies' parameter error.
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4", timeout: int = 30):
        """Initialize the handler with API credentials and settings."""
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.api_url = "https://api.openai.com/v1/chat/completions"
        
        # Validate the API key is present
        if not api_key:
            raise LLMAPIError("OpenAI API key is required")
            
        logger.info(f"Initialized Direct OpenAI handler with model {model}")
            
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(3)
    )
    def process_prompt(
        self,
        prompt: str,
        source: Optional[str] = None,
        language: Optional[str] = None,
        type: Optional[str] = None,
    ) -> str:
        """Process a prompt using direct API calls to OpenAI."""
        try:
            # Create messages for the API
            messages = self._create_messages(prompt, source, language, type)
            
            # Log the request (without full prompt for privacy)
            logger.info(
                "Sending request to OpenAI API",
                extra={
                    "model": self.model,
                    "prompt_length": len(prompt),
                    "source": source,
                    "language": language,
                    "type": type
                }
            )
            
            # Prepare the request payload
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 1024
            }
            
            # Set up headers with authentication
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Make the request directly using requests library
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            
            # Validate the response has the expected structure
            if not response_data.get("choices") or len(response_data["choices"]) == 0:
                raise LLMAPIError("Empty response from OpenAI API")
                
            # Get the message content
            message = response_data["choices"][0].get("message", {})
            content = message.get("content", "")
            
            if not content:
                raise LLMAPIError("Empty message content from OpenAI API")
                
            return content
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 0
            error_detail = ""
            
            try:
                error_data = e.response.json()
                error_detail = error_data.get("error", {}).get("message", str(e))
            except:
                error_detail = str(e)
                
            logger.error(f"HTTP error from OpenAI API: {status_code} - {error_detail}")
            
            if status_code == 401:
                raise LLMAPIError(f"Authentication error with OpenAI API: {error_detail}")
            elif status_code == 429:
                raise LLMAPIError(f"Rate limit exceeded with OpenAI API: {error_detail}")
            else:
                raise LLMAPIError(f"Error from OpenAI API: {error_detail}")
                
        except requests.exceptions.Timeout:
            logger.error("Request to OpenAI API timed out")
            raise LLMAPIError("Request to OpenAI API timed out")
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error with OpenAI API: {str(e)}")
            raise LLMAPIError(f"Connection error with OpenAI API: {str(e)}")
            
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
        """Create messages for the OpenAI API based on the parameters."""
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