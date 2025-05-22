from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional

class LLMParameters(BaseModel):
    """Schema for LLM parameters."""
    temperature: Optional[float] = Field(
        default=None, ge=0.0, le=1.0,
        description="Controls randomness in output (0.0 to 1.0)"
    )
    max_tokens: Optional[int] = Field(
        default=None, gt=0,
        description="Maximum number of tokens to generate"
    )
    top_p: Optional[float] = Field(
        default=None, ge=0.0, le=1.0,
        description="Nucleus sampling parameter (0.0 to 1.0)"
    )
    frequency_penalty: Optional[float] = Field(
        default=None, ge=-2.0, le=2.0,
        description="Penalty for token frequency (-2.0 to 2.0)"
    )
    presence_penalty: Optional[float] = Field(
        default=None, ge=-2.0, le=2.0,
        description="Penalty for token presence (-2.0 to 2.0)"
    )
    stop: Optional[list] = Field(
        default=None,
        description="List of strings to stop generation"
    )

class PromptRequest(BaseModel):
    """Schema for prompt processing request."""
    prompt: str = Field(..., description="The text to process")
    source: Optional[str] = Field(
        default="other", description="Source of the prompt"
    )
    language: Optional[str] = Field(
        default="en", description="Target language code (ISO 639-1)"
    )
    type: Optional[str] = Field(
        default="summary", description="Type of processing to perform"
    )
    parameters: Optional[LLMParameters] = Field(
        default=None, description="Custom parameters for the LLM"
    )

    @validator("prompt")
    def validate_prompt_length(cls, v):
        """Validate prompt length."""
        max_length = 4000
        if len(v) > max_length:
            raise ValueError(
                f"Prompt exceeds maximum length of {max_length} characters"
            )
        return v
