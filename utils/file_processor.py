# tests/unit/test_openrouter_handler.py
"""
Unit tests for OpenRouter handler.
"""
import pytest
from unittest.mock import patch, MagicMock
import httpx

from llm.openrouter_handler import OpenRouterHandler
from core.exceptions import LLMAPIError


class TestOpenRouterHandler:
    """Tests for OpenRouterHandler class."""

    @pytest.fixture
    def handler(self):
        """Create a handler instance for testing."""
        return OpenRouterHandler(api_key="test_key", model="openai/gpt-4o", timeout=5)

    @patch("httpx.Client.post")
    def test_process_prompt_success(self, mock_post, handler):
        """Test successful prompt processing."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Test response"
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        # Call the method
        result = handler.process_prompt(
            prompt="Test prompt",
            type="summary",
            source="email"
        )

        # Verify result
        assert result == "Test response"
        mock_post.assert_called_once()

    @patch("httpx.Client.post")
    def test_process_prompt_api_error(self, mock_post, handler):
        """Test handling of API errors."""
        # Mock the API error
        mock_post.side_effect = httpx.HTTPStatusError(
            "API error",
            request=MagicMock(),
            response=MagicMock(status_code=400, json=lambda: {"error": "Invalid request"})
        )

        # Call the method and verify exception
        with pytest.raises(LLMAPIError) as exc_info:
            handler.process_prompt(prompt="Test prompt")

        assert "OpenRouter API error: Invalid request" in str(exc_info.value)

    @patch("httpx.Client.post")
    def test_system_prompt_customization(self, mock_post, handler):
        """Test system prompt customization."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Test response"
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        # Call the method with different parameters
        handler.process_prompt(
            prompt="Test prompt",
            type="keywords",
            source="meeting"
        )

        # Get the payload sent to the API
        call_args = mock_post.call_args[1]
        payload = call_args["json"]
        messages = payload["messages"]
        system_message = messages[0]["content"] if messages and messages[0]["role"] == "system" else ""

        # Verify customization
        assert "meeting" in system_message.lower()
        assert "keywords" in system_message.lower()
