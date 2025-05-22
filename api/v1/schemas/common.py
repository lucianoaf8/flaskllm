# api/v1/schemas/common.py - Updated for Pydantic V2
"""
Common API Schemas Module - Updated for Pydantic V2

This module defines Pydantic schemas for request and response validation that are
common across multiple API endpoints.
"""
import re
from enum import Enum
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from flask import current_app
from pydantic import BaseModel, Field, field_validator, ValidationError

from core.constants import MAX_PROMPT_LENGTH
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
    """Schema for prompt processing request."""
    prompt: str = Field(
        ..., 
        description="The text to process",
        json_schema_extra={"example": "Summarize this meeting: we need to reduce hiring."}
    )
    source: Optional[PromptSource] = Field(
        default=PromptSource.OTHER, 
        description="Source of the prompt",
        json_schema_extra={"example": "meeting"}
    )
    language: Optional[str] = Field(
        default=None, 
        description="Target language code (ISO 639-1)",
        json_schema_extra={"example": "en"}
    )
    type: Optional[PromptType] = Field(
        default=PromptType.SUMMARY, 
        description="Type of processing to perform",
        json_schema_extra={"example": "summary"}
    )
    additional_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional parameters for the LLM provider"
    )

    @field_validator("prompt")
    @classmethod
    def validate_prompt_length(cls, v: str) -> str:
        """Validate prompt length against configured maximum."""
        # Get max_length from configuration if available
        try:
            settings = current_app.config.get("SETTINGS") if current_app else None
            max_length = getattr(settings, "max_prompt_length", MAX_PROMPT_LENGTH) if settings else MAX_PROMPT_LENGTH
        except RuntimeError:
            # Outside application context
            max_length = MAX_PROMPT_LENGTH
        
        if len(v) > max_length:
            raise ValueError(
                f"Prompt exceeds maximum length of {max_length} characters (current: {len(v)})"
            )
        if len(v.strip()) == 0:
            raise ValueError("Prompt cannot be empty or contain only whitespace")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        """Validate language code format using ISO 639-1 pattern."""
        if v is None:
            return v
            
        # ISO 639-1 language code pattern (e.g., 'en' or 'en-US')
        iso_pattern = re.compile(r'^[a-z]{2}(-[A-Z]{2})?$')
        
        if not isinstance(v, str) or not iso_pattern.match(v):
            raise ValueError(
                "Language must be a valid ISO 639-1 code (e.g., 'en' or 'en-US')"
            )
        return v


class ErrorDetail(BaseModel):
    """Detailed error information."""
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str = Field(..., description="Error message", json_schema_extra={"example": "Invalid input data"})
    code: Optional[str] = Field(None, description="Error code", json_schema_extra={"example": "VAL_2001"})
    details: Optional[List[ErrorDetail]] = Field(None, description="Detailed error information")


class PromptResponse(BaseModel):
    """Schema for prompt processing response."""
    result: str = Field(
        ..., 
        description="Processed result",
        json_schema_extra={"example": "The company plans to reduce hiring to cut costs."}
    )
    processing_time: float = Field(
        ..., 
        description="Processing time in seconds",
        json_schema_extra={"example": 1.25}
    )


class StreamingRequest(BaseModel):
    """Schema for streaming request."""
    prompt: str = Field(
        ..., 
        description="The text to process",
        json_schema_extra={"example": "Generate a story about a space adventure."}
    )
    max_tokens: Optional[int] = Field(
        default=1000,
        description="Maximum number of tokens to generate"
    )
    temperature: Optional[float] = Field(
        default=0.7,
        description="Sampling temperature"
    )


class GenericResponse(BaseModel):
    """Generic response envelope."""
    data: Dict[str, Any] = Field(..., description="Primary response data")
    meta: Optional[Dict[str, Any]] = Field(None, description="Response metadata")


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
        InvalidInputError: If validation fails with detailed error information
    """
    try:
        return schema_class(**data)
    except ValidationError as e:
        # Extract detailed validation errors
        error_details = []
        for error in e.errors():
            error_details.append({
                "field": "->".join(str(loc) for loc in error.get("loc", [])),
                "message": error.get("msg", "Unknown validation error"),
                "code": "VAL_" + error.get("type", "ERROR")
            })
            
        # Create a detailed error message
        if len(error_details) == 1:
            message = f"Validation error: {error_details[0]['message']}"
        else:
            message = f"Multiple validation errors ({len(error_details)})"
            
        raise InvalidInputError(message, error_details=error_details)
    except Exception as e:
        raise InvalidInputError(f"Invalid request data: {str(e)}")