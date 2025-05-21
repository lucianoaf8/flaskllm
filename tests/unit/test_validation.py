# tests/unit/test_validation.py
"""
Tests for the validation logic.
"""
import pytest
from pydantic import ValidationError

from api.v1.schemas import PromptRequest, PromptSource, PromptType, validate_request


class TestValidation:
    """Test suite for validation logic."""

    def test_prompt_request_valid(self):
        """Test valid PromptRequest validation."""
        # Minimal valid request
        data = {"prompt": "This is a test prompt"}
        request = validate_request(PromptRequest, data)
        assert request.prompt == "This is a test prompt"
        assert request.source == "other"  # Default value
        assert request.language == "en"  # Default value
        assert request.type == "summary"  # Default value

        # Complete valid request
        data = {
            "prompt": "This is a test prompt",
            "source": "email",
            "language": "fr",
            "type": "translation",
        }
        request = validate_request(PromptRequest, data)
        assert request.prompt == "This is a test prompt"
        assert request.source == "email"
        assert request.language == "fr"
        assert request.type == "translation"

    def test_prompt_request_invalid_prompt(self):
        """Test PromptRequest validation with invalid prompt."""
        # Empty prompt
        data = {"prompt": ""}
        with pytest.raises(ValidationError):
            validate_request(PromptRequest, data)

        # Missing prompt
        data = {"source": "email"}
        with pytest.raises(ValidationError):
            validate_request(PromptRequest, data)

        # Prompt too long (would need to adjust max_length in the schema)
        data = {"prompt": "x" * 10000}  # Assuming max length is less than this
        with pytest.raises(ValidationError):
            validate_request(PromptRequest, data)

    def test_prompt_request_invalid_source(self):
        """Test PromptRequest validation with invalid source."""
        # Invalid source
        data = {"prompt": "This is a test prompt", "source": "invalid_source"}
        with pytest.raises(ValidationError):
            validate_request(PromptRequest, data)

    def test_prompt_request_invalid_type(self):
        """Test PromptRequest validation with invalid type."""
        # Invalid type
        data = {"prompt": "This is a test prompt", "type": "invalid_type"}
        with pytest.raises(ValidationError):
            validate_request(PromptRequest, data)

    def test_prompt_request_invalid_language(self):
        """Test PromptRequest validation with invalid language."""
        # Invalid language code
        data = {"prompt": "This is a test prompt", "language": "invalid_language"}
        with pytest.raises(ValidationError):
            validate_request(PromptRequest, data)

        # Valid 2-letter language code
        data = {"prompt": "This is a test prompt", "language": "fr"}
        request = validate_request(PromptRequest, data)
        assert request.language == "fr"

    def test_prompt_source_enum(self):
        """Test PromptSource enum values."""
        assert PromptSource.EMAIL == "email"
        assert PromptSource.MEETING == "meeting"
        assert PromptSource.DOCUMENT == "document"
        assert PromptSource.CHAT == "chat"
        assert PromptSource.OTHER == "other"

    def test_prompt_type_enum(self):
        """Test PromptType enum values."""
        assert PromptType.SUMMARY == "summary"
        assert PromptType.KEYWORDS == "keywords"
        assert PromptType.SENTIMENT == "sentiment"
        assert PromptType.ENTITIES == "entities"
        assert PromptType.TRANSLATION == "translation"
        assert PromptType.CUSTOM == "custom"
