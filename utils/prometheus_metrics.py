# tests/integration/test_providers.py
"""
Integration tests for different LLM providers.
"""
import os
import pytest
from flask import current_app

from app import create_app
from core.config import Settings, LLMProvider
from llm.factory import get_llm_handler


@pytest.mark.skipif(not os.environ.get("XAI_API_KEY"), reason="XAI API key not available")
def test_xai_provider():
    """Test xAI provider with a real API call."""
    # Create app with xAI provider
    app = create_app(Settings(
        environment="testing",
        api_token="test_token",
        llm_provider=LLMProvider.XAI,
        xai_api_key=os.environ.get("XAI_API_KEY"),
        xai_model="grok-beta",
        request_timeout=30
    ))

    with app.app_context():
        # Get the handler
        handler = get_llm_handler(current_app.config["SETTINGS"])

        # Call the API
        result = handler.process_prompt(
            prompt="What is the capital of France?",
            type="summary"
        )

        # Verify result contains Paris
        assert "Paris" in result


@pytest.mark.skipif(not os.environ.get("OPENROUTER_API_KEY"), reason="OpenRouter API key not available")
def test_openrouter_provider():
    """Test OpenRouter provider with a real API call."""
    # Create app with OpenRouter provider
    app = create_app(Settings(
        environment="testing",
        api_token="test_token",
        llm_provider=LLMProvider.OPENROUTER,
        openrouter_api_key=os.environ.get("OPENROUTER_API_KEY"),
        openrouter_model="openai/gpt-4o",
        request_timeout=30
    ))

    with app.app_context():
        # Get the handler
        handler = get_llm_handler(current_app.config["SETTINGS"])

        # Call the API
        result = handler.process_prompt(
            prompt="What is the capital of Germany?",
            type="summary"
        )

        # Verify result contains Berlin
        assert "Berlin" in result
