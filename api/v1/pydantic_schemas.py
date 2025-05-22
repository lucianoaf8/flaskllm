# flaskllm/api/v1/pydantic_schemas.py
"""
Extended Pydantic Schemas Module

This module extends the core schemas from schemas.py with additional functionality
and parameters specific to LLM operations. It inherits from the base schemas to
maintain consistency while adding specialized fields and validation.

This separation allows the core schemas to remain focused on basic API validation,
while these extended schemas can evolve with more complex LLM-specific requirements.
"""

from flask import current_app
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional, Union

from api.v1.schemas import PromptRequest as BasePromptRequest
from api.v1.schemas import PromptSource, PromptType
from core.constants import MAX_PROMPT_LENGTH

class LLMParameters(BaseModel):
    """
    Schema for LLM parameters.
    
    This model defines the common parameters that can be passed to
    language models to control their behavior during text generation.
    Different LLM providers may support different subsets of these parameters.
    """
    temperature: Optional[float] = Field(
        default=None, ge=0.0, le=1.0,
        description="Controls randomness in output (0.0 to 1.0)",
        example=0.7
    )
    max_tokens: Optional[int] = Field(
        default=None, gt=0,
        description="Maximum number of tokens to generate",
        example=500
    )
    top_p: Optional[float] = Field(
        default=None, ge=0.0, le=1.0,
        description="Nucleus sampling parameter (0.0 to 1.0)",
        example=0.9
    )
    frequency_penalty: Optional[float] = Field(
        default=None, ge=-2.0, le=2.0,
        description="Penalty for token frequency (-2.0 to 2.0)",
        example=0.0
    )
    presence_penalty: Optional[float] = Field(
        default=None, ge=-2.0, le=2.0,
        description="Penalty for token presence (-2.0 to 2.0)",
        example=0.0
    )
    stop: Optional[List[str]] = Field(
        default=None,
        description="List of strings to stop generation",
        example=["\n", "###"]
    )
    
    class Config:
        """
        Pydantic configuration for LLMParameters.
        """
        extra = "forbid"  # Prevent extra fields not defined in the model

class ExtendedPromptRequest(BasePromptRequest):
    """
    Extended schema for prompt processing request with LLM parameters.
    
    This model extends the base PromptRequest from schemas.py by adding
    LLM-specific parameters while inheriting all the base validation
    and fields. This allows for more advanced LLM configuration while
    maintaining compatibility with the core API schema.
    """
    # Additional fields beyond the base PromptRequest
    parameters: Optional[LLMParameters] = Field(
        default=None, 
        description="Custom parameters for the LLM",
        example={"temperature": 0.7, "max_tokens": 500}
    )
    model: Optional[str] = Field(
        default=None,
        description="Specific LLM model to use, if supported by the provider",
        example="gpt-4"
    )
    stream: Optional[bool] = Field(
        default=False,
        description="Whether to stream the response or return it all at once",
        example=False
    )
    
    class Config:
        """
        Pydantic configuration for ExtendedPromptRequest.
        """
        schema_extra = {
            "example": {
                "prompt": "Summarize this meeting: we discussed budget cuts and new project timelines.",
                "source": "meeting",
                "type": "summary",
                "language": "en",
                "parameters": {
                    "temperature": 0.7,
                    "max_tokens": 500
                },
                "model": "gpt-4",
                "stream": False
            }
        }


# For backward compatibility, maintain the original name
PromptRequest = ExtendedPromptRequest
