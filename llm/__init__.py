# flaskllm/llm/__init__.py
"""
LLM Module

This module provides interfaces and implementations for various LLM providers
including OpenAI and Anthropic. It also includes conversation and template
management functionality.
"""

# Base handler and factory
from .base_llm_handler import BaseLLMHandler, CachedLLMHandler
from .factory import get_llm_handler

# Handler implementations
from .openai_handler import OpenAIHandler
from .openai_handler_v2 import OpenAIHandlerV2
from .openai_direct import OpenAIDirectHandler
from .anthropic_handler import AnthropicHandler

# Conversation and template models
from .conversation_storage import Conversation, Message, MessageRole
from .template_storage import PromptTemplate, TemplateVariable

__all__ = [
    # Base and factory
    'BaseLLMHandler',
    'CachedLLMHandler',
    'get_llm_handler',
    
    # Handler implementations
    'OpenAIHandler',
    'OpenAIHandlerV2',
    'OpenAIDirectHandler',
    'AnthropicHandler',
    
    # Conversation models
    'Conversation',
    'Message',
    'MessageRole',
    
    # Template models
    'PromptTemplate',
    'TemplateVariable',
]