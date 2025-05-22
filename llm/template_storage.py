# llm/templates.py
import re
import json
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from core.exceptions import TemplateError
from core.logging import get_logger

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
