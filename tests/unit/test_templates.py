# tests/unit/test_templates.py
import json
import os
import pytest
import tempfile
from unittest.mock import MagicMock

from llm.templates import PromptTemplate, TemplateVariable
from llm.template_storage import TemplateStorage

class TestPromptTemplate:
    """Test the PromptTemplate class."""
    
    def test_render_template(self):
        """Test rendering a template with variables."""
        # Create a template
        template = PromptTemplate(
            id="test_template",
            name="Test Template",
            description="A test template",
            template="Hello, {name}! You are {age} years old.",
            variables=[
                TemplateVariable(name="name", description="Your name", required=True),
                TemplateVariable(name="age", description="Your age", required=False, default="30")
            ]
        )
        
        # Render with all variables
        rendered = template.render({"name": "John", "age": "25"})
        assert rendered == "Hello, John! You are 25 years old."
        
        # Render with only required variables
        rendered = template.render({"name": "Alice"})
        assert rendered == "Hello, Alice! You are 30 years old."
        
        # Test missing required variable
        with pytest.raises(Exception):
            template.render({})

class TestTemplateStorage:
    """Test the TemplateStorage class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for templates."""
        with tempfile.TemporaryDirectory() as tmpdirname:
            yield tmpdirname
    
    @pytest.fixture
    def template_storage(self, temp_dir):
        """Create a template storage instance."""
        return TemplateStorage(templates_dir=temp_dir)
    
    def test_add_template(self, template_storage):
        """Test adding a template."""
        # Create a template
        template = PromptTemplate(
            id="test_template",
            name="Test Template",
            description="A test template",
            template="Hello, {name}!",
            variables=[
                TemplateVariable(name="name", description="Your name", required=True)
            ]
        )
        
        # Add template
        template_storage.add_template(template)
        
        # Verify template was added
        assert "test_template" in template_storage.templates
        assert template_storage.templates["test_template"].name == "Test Template"
    
    def test_get_template(self, template_storage):
        """Test getting a template."""
        # Add a template
        template = PromptTemplate(
            id="test_template",
            name="Test Template",
            description="A test template",
            template="Hello, {name}!",
            variables=[
                TemplateVariable(name="name", description="Your name", required=True)
            ]
        )
        template_storage.add_template(template)
        
        # Get template
        retrieved = template_storage.get_template("test_template")
        
        # Verify template
        assert retrieved.id == "test_template"
        assert retrieved.name == "Test Template"
