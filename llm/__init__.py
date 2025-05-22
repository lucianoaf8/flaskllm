# flaskllm/llm/__init__.py
"""
LLM Module

This module provides interfaces and implementations for various LLM providers
including OpenAI and Anthropic. It also includes conversation and template
management functionality.
"""

from .factory import get_llm_handler, LLMProvider
from .base_llm_handler import BaseLLMHandler
from .handlers import OpenAIHandler, AnthropicHandler, OpenRouterHandler
from .storage import ConversationStorage, TemplateStorage

__all__ = [
    'get_llm_handler', 'LLMProvider',
    'BaseLLMHandler', 
    'OpenAIHandler', 'AnthropicHandler', 'OpenRouterHandler',
    'ConversationStorage', 'TemplateStorage'
]