# tests/unit/test_openai_handler.py
"""
Unit tests for OpenAI handler.
"""
from unittest.mock import MagicMock, patch

import openai
import pytest

from api.v1.schemas import PromptSource, PromptType
from core.exceptions import LLMAPIError
from llm.openai_handler import OpenAIHandler


class TestOpenAIHandler:
    """Tests for OpenAIHandler class."""

    @pytest.fixture
    def handler(self):
        """Create a handler instance for testing."""
        return OpenAIHandler(api_key="test_key", model="gpt-3.5-turbo", timeout=5)

    @patch("openai.OpenAI")
    def test_process_prompt_success(self, mock_openai, handler):
        """Test successful prompt processing."""
        # Mock the API response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]
        mock_client.chat.completions.create.return_value = mock_response

        # Call the method
        result = handler.process_prompt(
            prompt="Test prompt", type=PromptType.SUMMARY, source=PromptSource.EMAIL
        )

        # Verify result
        assert result == "Test response"
        mock_client.chat.completions.create.assert_called_once()

    @patch("openai.OpenAI")
    def test_process_prompt_api_error(self, mock_openai, handler):
        """Test handling of API errors."""
        # Mock the API error
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = openai.APIError("API error")

        # Call the method and verify exception
        with pytest.raises(LLMAPIError) as exc_info:
            handler.process_prompt(prompt="Test prompt")

        assert "API error" in str(exc_info.value)

    @patch("openai.OpenAI")
    def test_system_prompt_customization(self, mock_openai, handler):
        """Test system prompt customization."""
        # Mock the API response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]
        mock_client.chat.completions.create.return_value = mock_response

        # Call the method with different parameters
        handler.process_prompt(
            prompt="Test prompt", type=PromptType.KEYWORDS, source=PromptSource.MEETING
        )

        # Verify the system prompt was customized correctly
        call_args = mock_client.chat.completions.create.call_args[1]
        messages = call_args["messages"]
        system_message = messages[0]["content"]

        assert "meeting" in system_message.lower()
        assert "keywords" in system_message.lower()
