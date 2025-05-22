# flaskllm/core/xai_config.py
"""
Explainable AI (XAI) Configuration Module

This module defines configuration options and utilities for adding explainability
to LLM responses. It provides settings for controlling how explanations are generated,
formatted, and presented to users.

Explainability features help users understand model outputs by providing:
- Confidence scores for different parts of the response
- Sources and citations for factual claims
- Alternative responses that were considered
- Explanation of the reasoning process
"""

from enum import Enum
from typing import Dict, List, Optional, Union, Any

from pydantic import BaseModel, Field, validator


class ExplanationLevel(str, Enum):
    """Level of explanation detail to provide."""
    
    NONE = "none"       # No explanation
    MINIMAL = "minimal" # Basic confidence scores only
    STANDARD = "standard" # Standard explanation with reasoning highlights
    DETAILED = "detailed" # Detailed explanation with citations and alternatives


class ExplanationFormat(str, Enum):
    """Format for presenting explanations."""
    
    TEXT = "text"       # Plain text explanation
    HTML = "html"       # HTML formatted explanation with highlighting
    JSON = "json"       # Structured JSON explanation for programmatic use
    MARKDOWN = "markdown" # Markdown formatted explanation


class SourceType(str, Enum):
    """Types of sources that can be cited in explanations."""
    
    DOCUMENT = "document" # Document in knowledge base
    WEBPAGE = "webpage"   # Web page
    DATASET = "dataset"   # Training dataset
    MODEL = "model"       # Model knowledge
    CALCULATION = "calculation" # Mathematical calculation
    REASONING = "reasoning" # Logical reasoning


class ConfidenceScoring(BaseModel):
    """Configuration for confidence scoring in explanations."""
    
    enabled: bool = True
    min_threshold: float = 0.3  # Minimum confidence to include in response
    highlight_threshold: float = 0.7  # Threshold for highlighting high confidence
    include_scores_in_output: bool = False  # Whether to include scores in the output

    @validator('min_threshold', 'highlight_threshold')
    def validate_threshold(cls, v):
        """Validate that thresholds are between 0 and 1."""
        if v < 0 or v > 1:
            raise ValueError('Threshold must be between 0 and 1')
        return v


class CitationSettings(BaseModel):
    """Configuration for citations in explanations."""
    
    enabled: bool = True
    link_sources: bool = True  # Include links to sources when available
    max_sources: int = 5       # Maximum number of sources to cite
    required_for_facts: bool = True  # Require citations for factual claims
    source_types: List[SourceType] = Field(
        default_factory=lambda: [t for t in SourceType]
    )  # Allowed source types


class AlternativeResponseSettings(BaseModel):
    """Configuration for including alternative responses in explanations."""
    
    enabled: bool = False
    max_alternatives: int = 2  # Maximum number of alternatives to include
    min_confidence_delta: float = 0.1  # Minimum confidence difference to include


class XAISettings(BaseModel):
    """Main configuration for Explainable AI features."""
    
    enabled: bool = True
    explanation_level: ExplanationLevel = ExplanationLevel.STANDARD
    explanation_format: ExplanationFormat = ExplanationFormat.MARKDOWN
    confidence_scoring: ConfidenceScoring = Field(default_factory=ConfidenceScoring)
    citation_settings: CitationSettings = Field(default_factory=CitationSettings)
    alternative_responses: AlternativeResponseSettings = Field(
        default_factory=AlternativeResponseSettings
    )
    include_model_info: bool = True  # Include model name and version in explanation
    include_token_usage: bool = False  # Include token usage in explanation
    include_processing_time: bool = True  # Include processing time in explanation


def get_default_xai_settings() -> XAISettings:
    """Get default XAI settings.
    
    Returns:
        Default XAI settings
    """
    return XAISettings()


def get_minimal_xai_settings() -> XAISettings:
    """Get minimal XAI settings with basic explainability only.
    
    Returns:
        Minimal XAI settings
    """
    return XAISettings(
        explanation_level=ExplanationLevel.MINIMAL,
        confidence_scoring=ConfidenceScoring(
            include_scores_in_output=False
        ),
        citation_settings=CitationSettings(
            enabled=False
        ),
        alternative_responses=AlternativeResponseSettings(
            enabled=False
        ),
        include_model_info=False,
        include_token_usage=False,
        include_processing_time=False
    )


def get_detailed_xai_settings() -> XAISettings:
    """Get detailed XAI settings with maximum explainability.
    
    Returns:
        Detailed XAI settings
    """
    return XAISettings(
        explanation_level=ExplanationLevel.DETAILED,
        explanation_format=ExplanationFormat.HTML,
        confidence_scoring=ConfidenceScoring(
            include_scores_in_output=True
        ),
        citation_settings=CitationSettings(
            max_sources=10
        ),
        alternative_responses=AlternativeResponseSettings(
            enabled=True,
            max_alternatives=3
        ),
        include_model_info=True,
        include_token_usage=True,
        include_processing_time=True
    )
