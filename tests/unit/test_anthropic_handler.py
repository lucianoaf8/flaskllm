# tests/unit/test_anthropic_handler.py
"""
Tests for the Anthropic LLM handler.
"""
from unittest.mock import MagicMock, patch

import pytest

from api.v1.schemas.common import PromptSource, PromptType
from core.exceptions import LLMAPIError

# Mock anthropic module if not installed
try:
    import anthropic
except ImportError:
    import sys
    from unittest.mock import MagicMock
    sys.modules['anthropic'] = MagicMock()
    anthropic = sys.modules['anthropic']
    Exception = Exception
    Exception = Exception  
    Exception = Exception

from llm.handlers.anthropic import AnthropicHandler


class TestAnthropicHandler:
    """Test suite for AnthropicHandler class."""

    @pytest.fixture
    def handler(self):
        """Create an AnthropicHandler for testing."""
        return AnthropicHandler(api_key="test_key", model="claude-2")

    @patch("anthropic.Anthropic")
    def test_process_prompt_success(self, mock_anthropic, handler):
        """Test successful prompt processing."""
        # Setup mock response
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_content = MagicMock()
        mock_content.type = "text"
        mock_content.text = "Test response"

        mock_response = MagicMock()
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response

        # Call the method
        result = handler.process_prompt("Test prompt")

        # Verify result
        assert result == "Test response"
        mock_client.messages.create.assert_called_once()
        # Verify parameters passed to the API
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "claude-2"
        assert call_kwargs["messages"][0]["content"] == "Test prompt"
        assert "system" in call_kwargs

    @patch("anthropic.Anthropic")
    def test_process_prompt_with_parameters(self, mock_anthropic, handler):
        """Test prompt processing with source, language, type parameters."""
        # Setup mock
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_content = MagicMock()
        mock_content.type = "text"
        mock_content.text = "Test translation"

        mock_response = MagicMock()
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response

        # Call the method with additional parameters
        result = handler.process_prompt(
            prompt="Translate this text",
            source=PromptSource.EMAIL,
            language="es",
            type=PromptType.TRANSLATION,
        )

        # Verify result
        assert result == "Test translation"

        # Verify system prompt includes the parameters
        call_kwargs = mock_client.messages.create.call_args.kwargs
        system_prompt = call_kwargs["system"]
        assert "email" in system_prompt.lower()
        assert "translate" in system_prompt.lower()
        assert "spanish" in system_prompt.lower() or "es" in system_prompt.lower()

    @patch("anthropic.Anthropic")
    def test_process_prompt_empty_response(self, mock_anthropic, handler):
        """Test handling of empty response from API."""
        # Setup mock with empty response
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = []
        mock_client.messages.create.return_value = mock_response

        # Verify exception is raised
        with pytest.raises(LLMAPIError, match="Empty response"):
            handler.process_prompt("Test prompt")

    @patch("anthropic.Anthropic")
    def test_process_prompt_api_error(self, mock_anthropic, handler):
        """Test handling of API error."""
        # Setup mock to raise an API error
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API Error")

        # Verify exception is raised and wrapped
        with pytest.raises(LLMAPIError, match="Error from Anthropic API"):
            handler.process_prompt("Test prompt")

    @patch("anthropic.Anthropic")
    def test_process_prompt_auth_error(self, mock_anthropic, handler):
        """Test handling of authentication error."""
        # Setup mock to raise an auth error
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.side_effect = Exception(
            "Auth Error"
        )

        # Verify exception is raised and wrapped
        with pytest.raises(LLMAPIError, match="Authentication error"):
            handler.process_prompt("Test prompt")

    @patch("anthropic.Anthropic")
    def test_process_prompt_rate_limit_error(self, mock_anthropic, handler):
        """Test handling of rate limit error."""
        # Setup mock to raise a rate limit error
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.side_effect = Exception(
            "Rate limit exceeded"
        )

        # Verify exception is raised and wrapped
        with pytest.raises(LLMAPIError, match="Rate limit exceeded"):
            handler.process_prompt("Test prompt")

    def test_create_system_prompt(self, handler):
        """Test system prompt creation with different parameters."""
        # Test base prompt
        prompt = handler._create_system_prompt()
        assert "AI assistant" in prompt

        # Test email source
        prompt = handler._create_system_prompt(source=PromptSource.EMAIL)
        assert "email" in prompt.lower()

        # Test meeting source
        prompt = handler._create_system_prompt(source=PromptSource.MEETING)
        assert "meeting" in prompt.lower()

        # Test document source
        prompt = handler._create_system_prompt(source=PromptSource.DOCUMENT)
        assert "document" in prompt.lower()

        # Test summary type
        prompt = handler._create_system_prompt(type=PromptType.SUMMARY)
        assert "summary" in prompt.lower()

        # Test keywords type
        prompt = handler._create_system_prompt(type=PromptType.KEYWORDS)
        assert "keywords" in prompt.lower()

        # Test sentiment type
        prompt = handler._create_system_prompt(type=PromptType.SENTIMENT)
        assert "sentiment" in prompt.lower()

        # Test entities type
        prompt = handler._create_system_prompt(type=PromptType.ENTITIES)
        assert "entities" in prompt.lower()

        # Test translation type with language
        prompt = handler._create_system_prompt(
            type=PromptType.TRANSLATION, language="fr"
        )
        assert "translate" in prompt.lower()
        assert "french" in prompt.lower() or "fr" in prompt.lower()

        # Test language parameter
        prompt = handler._create_system_prompt(language="de")
        assert (
            "german" in prompt.lower()
            or "de" in prompt.lower()
            or "respond in" in prompt.lower()
        )
