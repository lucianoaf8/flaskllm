# flaskllm/api/v1/schemas.py
"""
API Schemas Module

This module defines Pydantic schemas for request and response validation.
"""
from enum import Enum
from typing import Any, Dict, Optional, Type, TypeVar

from pydantic import BaseModel, Field, validator

from core.exceptions import InvalidInputError


class PromptSource(str, Enum):
    """Source of the prompt."""

    EMAIL = "email"
    MEETING = "meeting"
    DOCUMENT = "document"
    CHAT = "chat"
    OTHER = "other"


class PromptType(str, Enum):
    """Type of processing to perform."""

    SUMMARY = "summary"
    KEYWORDS = "keywords"
    SENTIMENT = "sentiment"
    ENTITIES = "entities"
    TRANSLATION = "translation"
    CUSTOM = "custom"


class PromptRequest(BaseModel):
    """
    Schema for prompt processing request.
    """

    prompt: str = Field(..., description="The text to process")
    source: Optional[PromptSource] = Field(
        default=None, description="Source of the prompt"
    )
    language: Optional[str] = Field(
        default=None, description="Target language code (ISO 639-1)"
    )
    type: Optional[PromptType] = Field(
        default=None, description="Type of processing to perform"
    )

    @validator("prompt")
    def validate_prompt_length(cls, v, values, **kwargs):
        """Validate prompt length."""
        # Note: In a real app, you'd get max_length from config
        max_length = 4000
        if len(v) > max_length:
            raise ValueError(
                f"Prompt exceeds maximum length of {max_length} characters"
            )
        return v

    @validator("language")
    def validate_language(cls, v):
        """Validate language code format."""
        if v is not None and (not isinstance(v, str) or len(v) not in [2, 5]):
            raise ValueError(
                "Language must be a valid ISO 639-1 code (e.g., 'en' or 'en-US')"
            )
        return v


class PromptResponse(BaseModel):
    """
    Schema for prompt processing response.
    """

    summary: str = Field(..., description="Processed result")
    processing_time: float = Field(..., description="Processing time in seconds")


# Generic type for schema validation
T = TypeVar("T", bound=BaseModel)


def validate_request(schema_class: Type[T], data: Dict[str, Any]) -> T:
    """
    Validate request data against a Pydantic schema.

    Args:
        schema_class: Pydantic model class to validate against
        data: Request data to validate

    Returns:
        Validated Pydantic model instance

    Raises:
        InvalidInputError: If validation fails
    """
    try:
        return schema_class(**data)
    except Exception as e:
        raise InvalidInputError(f"Invalid request data: {str(e)}")
