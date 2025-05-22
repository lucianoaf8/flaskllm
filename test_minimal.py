#!/usr/bin/env python3
"""
test_minimal.py - Minimal test suite to verify basic functionality
"""

import os
os.environ.update({
    "ENVIRONMENT": "testing",
    "API_TOKEN": "test_token",
    "OPENAI_API_KEY": "test_key",
    "LLM_PROVIDER": "openai",
    "RATE_LIMIT_ENABLED": "False",
    "DEBUG": "True"
})

import pytest
from flask import Flask

def test_app_creation():
    """Test that the app can be created."""
    from app import create_app
    
    app = create_app()
    assert app is not None
    assert isinstance(app, Flask)

def test_health_endpoint():
    """Test the health check endpoint."""
    from app import create_app
    
    app = create_app()
    client = app.test_client()
    
    response = client.get("/api/v1/core/health")
    assert response.status_code == 200
    
    data = response.get_json()
    assert data["status"] == "ok"

def test_config_loading():
    """Test configuration loading."""
    from core.config import Settings, LLMProvider
    
    settings = Settings(
        api_token="test_token",
        openai_api_key="test_key",
        llm_provider=LLMProvider.OPENAI
    )
    
    assert settings.api_token == "test_token"
    assert settings.openai_api_key == "test_key"
    assert settings.llm_provider == LLMProvider.OPENAI

def test_prompt_schema():
    """Test prompt request schema."""
    from api.v1.schemas.common import PromptRequest, PromptType, PromptSource
    
    # Valid request
    request = PromptRequest(
        prompt="Test prompt",
        type=PromptType.SUMMARY,
        source=PromptSource.EMAIL
    )
    
    assert request.prompt == "Test prompt"
    assert request.type == PromptType.SUMMARY
    assert request.source == PromptSource.EMAIL

def test_authentication_required():
    """Test that authentication is required for protected endpoints."""
    from app import create_app
    
    app = create_app()
    client = app.test_client()
    
    # Without token
    response = client.post("/api/v1/core/webhook", json={"prompt": "test"})
    assert response.status_code == 401
    
    # With token
    response = client.post(
        "/api/v1/core/webhook",
        json={"prompt": "test"},
        headers={"X-API-Token": "test_token"}
    )
    # Should not be 401 (might be 502 if LLM fails, but that's ok)
    assert response.status_code != 401

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
