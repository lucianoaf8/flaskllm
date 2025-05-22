# llm/storage/templates.py
import re
import json
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from core.exceptions import APIError
from core.logging import get_logger

# Configure logger
logger = get_logger(__name__)

class TemplateVariable(BaseModel):
    """Model for a template variable."""
    name: str = Field(..., description="Variable name")
    description: str = Field(..., description="Variable description")
    required: bool = Field(default=False, description="Whether the variable is required")
    default: Optional[str] = Field(default=None, description="Default value if not provided")

class PromptTemplate(BaseModel):
    """Model for a prompt template."""
    id: str = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    template: str = Field(..., description="Template text with variables")
    variables: List[TemplateVariable] = Field(default_factory=list, description="Template variables")
    system_prompt: Optional[str] = Field(default=None, description="System prompt for this template")
    type: Optional[str] = Field(default=None, description="Template type")
    source: Optional[str] = Field(default=None, description="Template source")
    language: Optional[str] = Field(default=None, description="Template language")

    def render(self, variables: Dict[str, Any]) -> str:
        """
        Render the template with the provided variables.

        Args:
            variables: Dictionary of variable values

        Returns:
            Rendered template

        Raises:
            TemplateError: If required variables are missing
        """
        rendered = self.template

        # Check for missing required variables
        missing_vars = []
        for var in self.variables:
            if var.required and var.name not in variables and var.default is None:
                missing_vars.append(var.name)

        if missing_vars:
            raise TemplateError(f"Missing required variables: {', '.join(missing_vars)}")

        # Render variables in the template
        for var in self.variables:
            value = variables.get(var.name, var.default or "")
            rendered = rendered.replace(f"{{{var.name}}}", str(value))

        # Return the rendered template
        return rendered


class TemplateStorage:
    """Storage for templates."""

    def __init__(self, db_client=None):
        """
        Initialize template storage.

        Args:
            db_client: Database client (if None, uses in-memory storage)
        """
        self.db_client = db_client
        self.templates: Dict[str, PromptTemplate] = {}
        logger.info("Template storage initialized")

    def create_template(self, template: PromptTemplate) -> PromptTemplate:
        """
        Create a new template.

        Args:
            template: Template to create

        Returns:
            Created template
        """
        self.templates[template.id] = template
        logger.info(
            "Created new template",
            template_id=template.id,
            template_name=template.name
        )
        return template

    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """
        Get a template by ID.

        Args:
            template_id: Template ID

        Returns:
            Template or None if not found
        """
        return self.templates.get(template_id)

    def update_template(self, template: PromptTemplate) -> None:
        """
        Update a template.

        Args:
            template: Template to update
        """
        self.templates[template.id] = template
        logger.info(
            "Updated template",
            template_id=template.id,
            template_name=template.name
        )

    def delete_template(self, template_id: str) -> bool:
        """
        Delete a template.

        Args:
            template_id: Template ID

        Returns:
            True if deleted, False if not found
        """
        if template_id in self.templates:
            del self.templates[template_id]
            logger.info(
                "Deleted template",
                template_id=template_id
            )
            return True
        return False

    def get_all_templates(self) -> List[PromptTemplate]:
        """
        Get all templates.

        Returns:
            List of all templates
        """
        return list(self.templates.values())
