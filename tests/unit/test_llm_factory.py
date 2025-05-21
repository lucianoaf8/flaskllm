# tests/unit/test_llm_factory.py
"""
Tests for the LLM factory module.
"""
import pytest
from unittest.mock import patch

from llm.factory import get_llm_handler
from core.config import Settings, LLMProvider
from core.exceptions import LLMAPIError
from llm.openai_handler import OpenAIHandler
from llm.anthropic_handler import AnthropicHandler


class TestLLMFactory:
    """Test suite for LLM factory."""

    def test_get_llm_handler_openai(self):
        """Test getting OpenAI handler."""
        # Create settings with OpenAI configuration
        settings = Settings(
            llm_provider=LLMProvider.OPENAI,
            openai_api_key="test_key",
            openai_model="gpt-4",
            request_timeout=30
        )

        # Get handler
        with patch("llm.factory.OpenAIHandler") as mock_openai:
            handler = get_llm_handler(settings)
            
            # Verify OpenAIHandler was created with correct parameters
            mock_openai.assert_called_once_with(
                api_key="test_key",
                model="gpt-4",
                timeout=30
            )

    def test_get_llm_handler_anthropic(self):
        """Test getting Anthropic handler."""
        # Create settings with Anthropic configuration
        settings = Settings(
            llm_provider=LLMProvider.ANTHROPIC,
            anthropic_api_key="test_key",
            anthropic_model="claude-2",
            request_timeout=30
        )

        # Get handler
        with patch("llm.factory.AnthropicHandler") as mock_anthropic:
            handler = get_llm_handler(settings)
            
            # Verify AnthropicHandler was created with correct parameters
            mock_anthropic.assert_called_once_with(
                api_key="test_key",
                model="claude-2",
                timeout=30
            )

    def test_get_llm_handler_openai_missing_key(self):
        """Test error when OpenAI API key is missing."""
        # Create settings with missing API key
        settings = Settings(
            llm_provider=LLMProvider.OPENAI,
            openai_api_key=None,
            openai_model="gpt-4"
        )

        # Verify exception is raised
        with pytest.raises(LLMAPIError, match="OpenAI API key is not configured"):
            get_llm_handler(settings)

    def test_get_llm_handler_anthropic_missing_key(self):
        """Test error when Anthropic API key is missing."""
        # Create settings with missing API key
        settings = Settings(
            llm_provider=LLMProvider.ANTHROPIC,
            anthropic_api_key=None,
            anthropic_model="claude-2"
        )

        # Verify exception is raised
        with pytest.raises(LLMAPIError, match="Anthropic API key is not configured"):
            get_llm_handler(settings)

    def test_get_llm_handler_unsupported_provider(self):
        """Test error with unsupported provider."""
        # Create settings with invalid provider
        settings = Settings(
            llm_provider="invalid_provider"
        )

        # Verify exception is raised
        with pytest.raises(LLMAPIError, match="Unsupported LLM provider"):
            get_llm_handler(settings)

    @patch("llm.factory.OpenAIHandler")
    def test_handler_implements_protocol(self, mock_openai_handler):
        """Test that handlers implement the LLMHandler protocol."""
        # Setup mock
        handler_instance = mock_openai_handler.return_value
        handler_instance.process_prompt.return_value = "test response"
        
        # Create settings
        settings = Settings(
            llm_provider=LLMProvider.OPENAI,
            openai_api_key="test_key"
        )
        
        # Get handler
        handler = get_llm_handler(settings)
        
        # Call process_prompt to verify it works
        result = handler.process_prompt("test prompt")
        assert result == "test response"
        handler_instance.process_prompt.assert_called_once_with(
            prompt="test prompt", source=None, language=None, type=None
        )