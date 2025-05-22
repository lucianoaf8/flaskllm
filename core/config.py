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
    XAI = "xai"
    OPEN_ROUTINE = "open_routine"
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

    # XAI settings (optional)
    xai_api_key: Optional[str] = Field(default=None, description="XAI API key")

    # Open Routine settings (optional)
    open_routine_api_key: Optional[str] = Field(
        default=None, description="Open Routine API key"
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

    # -------------------------------------------------
    # Cache settings
    # -------------------------------------------------
    class CacheBackendType(str, Enum):
        MEMORY = "memory"      # in‑process dict (default)
        FILE   = "file"        # pickled files in a local folder
        REDIS  = "redis"       # external Redis server
        MYSQL  = "mysql"       # external MySQL server

    cache_enabled: bool = Field(
        default=True, description="Enable/disable request‑level caching"
    )
    cache_backend: CacheBackendType = Field(
        default=CacheBackendType.MEMORY,
        description="Caching backend: memory | file | redis",
    )
    cache_expiration: int = Field(
        default=86_400, description="TTL for cached items (seconds)"
    )
    cache_max_size: int = Field(
        default=10_000, description="Max cached items (only for memory/file)"
    )
    cache_dir: str = Field(
        default=".cache", description="Directory for the FILE backend"
    )
    redis_url: Optional[str] = Field(
        default="redis://localhost:6379/0", description="Redis URL for the REDIS backend"
    )
    mysql_url: Optional[str] = Field(
        default=None,
        description="SQLAlchemy URL for MySQL cache (e.g. mysql+pymysql://user:pass@host/db/db)"
    )

    # Token management settings
    token_db_path: str = Field(
        default="data/tokens.db", 
        description="Path to token database"
    )
    token_encryption_key: Optional[str] = Field(
        default=None, 
        description="Encryption key for token storage"
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

    @validator("xai_api_key")
    def validate_xai_api_key(cls, v, values):
        """Validate that XAI API key is provided when XAI is selected."""
        if values.get("llm_provider") == LLMProvider.XAI and not v:
            raise ValueError("XAI API key is required when using XAI provider")
        return v

    @validator("open_routine_api_key")
    def validate_open_routine_api_key(cls, v, values):
        """Validate that Open Routine API key is provided when Open Routine is selected."""
        if values.get("llm_provider") == LLMProvider.OPEN_ROUTINE and not v:
            raise ValueError(
                "Open Routine API key is required when using Open Routine provider"
            )
        return v

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def get_settings() -> Settings:
    """
    Create and return Settings instance from environment variables.

    Returns:
        Settings object with configuration values
    """
    return Settings()
