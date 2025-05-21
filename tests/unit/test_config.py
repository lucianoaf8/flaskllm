# flaskllm/tests/unit/test_config.py
"""
Tests for configuration module.
"""
import os
from unittest.mock import patch

import pytest

from core.config import EnvironmentType, LLMProvider, Settings


def test_default_settings():
    """Test default settings values."""
    # Set required environment variables
    with patch.dict(
        os.environ, {"API_TOKEN": "test_token", "OPENAI_API_KEY": "test_key"}
    ):
        settings = Settings()

        assert settings.environment == EnvironmentType.DEVELOPMENT
        assert settings.debug is False
        assert settings.api_token == "test_token"
        assert settings.allowed_origins == "*"
        assert settings.llm_provider == LLMProvider.OPENAI
        assert settings.openai_api_key == "test_key"
        assert settings.openai_model == "gpt-4"
        assert settings.request_timeout == 30
        assert settings.max_prompt_length == 4000
        assert settings.rate_limit_enabled is True
        assert settings.rate_limit == 60


def test_environment_variables_override():
    """Test that environment variables override defaults."""
    # Set environment variables
    env_vars = {
        "ENVIRONMENT": "production",
        "DEBUG": "True",
        "API_TOKEN": "env_token",
        "ALLOWED_ORIGINS": "domain1.com,domain2.com",
        "LLM_PROVIDER": "openai",
        "OPENAI_API_KEY": "env_openai_key",
        "OPENAI_MODEL": "gpt-3.5-turbo",
        "REQUEST_TIMEOUT": "60",
        "MAX_PROMPT_LENGTH": "8000",
        "RATE_LIMIT_ENABLED": "False",
        "RATE_LIMIT": "120",
    }

    with patch.dict(os.environ, env_vars):
        settings = Settings()

        assert settings.environment == EnvironmentType.PRODUCTION
        assert settings.debug is True
        assert settings.api_token == "env_token"
        assert settings.allowed_origins == ["domain1.com", "domain2.com"]
        assert settings.llm_provider == LLMProvider.OPENAI
        assert settings.openai_api_key == "env_openai_key"
        assert settings.openai_model == "gpt-3.5-turbo"
        assert settings.request_timeout == 60
        assert settings.max_prompt_length == 8000
        assert settings.rate_limit_enabled is False
        assert settings.rate_limit == 120


def test_validation_openai_api_key():
    """Test validation of OpenAI API key."""
    # Missing OpenAI API key
    with patch.dict(os.environ, {"API_TOKEN": "test_token", "LLM_PROVIDER": "openai"}):
        with pytest.raises(ValueError) as excinfo:
            Settings()
        assert "OpenAI API key is required" in str(excinfo.value)


def test_validation_anthropic_api_key():
    """Test validation of Anthropic API key."""
    # Missing Anthropic API key
    with patch.dict(
        os.environ, {"API_TOKEN": "test_token", "LLM_PROVIDER": "anthropic"}
    ):
        with pytest.raises(ValueError) as excinfo:
            Settings()
        assert "Anthropic API key is required" in str(excinfo.value)
