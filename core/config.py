# flaskllm/core/config.py
"""
Configuration Management Module

This module provides settings management using Pydantic for validation
and dotenv for environment variable loading.
"""
from enum import Enum
from typing import List, Optional, Union

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class EnvironmentType(str, Enum):
    """Environment types for the application."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    # Add other providers as needed


class Settings(BaseSettings):
    """
    Application settings with validation.

    This class manages all configuration settings for the application,
    loading from environment variables with appropriate validation.
    """

    # Environment settings
    environment: EnvironmentType = Field(
        default=EnvironmentType.DEVELOPMENT, description="Application environment"
    )
    debug: bool = Field(default=False, description="Enable debug mode")

    # API security settings
    api_token: str = Field(description="Authentication token for API access")
    allowed_origins: Union[str, List[str]] = Field(
        default="*", description="CORS allowed origins (comma-separated if multiple)"
    )

    # LLM settings
    llm_provider: LLMProvider = Field(
        default=LLMProvider.OPENAI, description="LLM provider to use"
    )
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    openai_model: str = Field(default="gpt-4", description="OpenAI model to use")

    # Anthropic settings (optional)
    anthropic_api_key: Optional[str] = Field(
        default=None, description="Anthropic API key"
    )
    anthropic_model: str = Field(
        default="claude-2", description="Anthropic model to use"
    )

    # Request configuration
    request_timeout: int = Field(
        default=30, description="Timeout for LLM API requests in seconds"
    )
    max_prompt_length: int = Field(
        default=4000, description="Maximum allowed prompt length"
    )

    # Rate limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit: int = Field(
        default=60, description="Number of requests allowed per minute"
    )

    @validator("allowed_origins", pre=True)
    def parse_allowed_origins(cls, v):
        """Parse allowed origins from string to list if needed."""
        if isinstance(v, str) and v != "*":
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("openai_api_key")
    def validate_openai_api_key(cls, v, values):
        """Validate that OpenAI API key is provided when OpenAI is selected."""
        if values.get("llm_provider") == LLMProvider.OPENAI and not v:
            raise ValueError("OpenAI API key is required when using OpenAI provider")
        return v

    @validator("anthropic_api_key")
    def validate_anthropic_api_key(cls, v, values):
        """Validate that Anthropic API key is provided when Anthropic is selected."""
        if values.get("llm_provider") == LLMProvider.ANTHROPIC and not v:
            raise ValueError(
                "Anthropic API key is required when using Anthropic provider"
            )
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


def get_settings() -> Settings:
    """
    Create and return Settings instance from environment variables.

    Returns:
        Settings object with configuration values
    """
    return Settings()
