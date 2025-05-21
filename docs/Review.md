---
created: 2025-05-21T01:18:45 (UTC -06:00)
tags: []
source: https://claude.ai/chat/f9f8d1e9-9a0f-413b-8441-3c1dcb25438f
author: 
---

# Review Task List for Next Phase of Flask LLM API - Claude

> ## Excerpt
> Talk with Claude, an AI assistant from Anthropic

---
```
python               'assistant_message': {
                   'id': assistant_message.id,
                   'role': assistant_message.role,
                   'content': assistant_message.content,
                   'timestamp': assistant_message.timestamp.isoformat()
               }
           })
   except ConversationError as e:
       return jsonify({
           'error': 'Conversation not found',
           'details': str(e),
           'code': 'NOT_FOUND'
       }), 404
   except Exception as e:
       logger.error(f"Error adding message: {str(e)}", exc_info=True)
       return jsonify({
           'error': 'Server Error',
           'details': str(e),
           'code': 'SERVER_ERROR'
       }), 500
```

### 6\. Implement User-Specific Customizations

Finally, let's create a system for user-specific settings and customizations.

#### Create User Settings Model

```
python# core/user_settings.py
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from uuid import uuid4

from pydantic import BaseModel, Field

class LLMSettings(BaseModel):
    """LLM settings for a user."""
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)

class UISettings(BaseModel):
    """UI settings for a user."""
    theme: Optional[str] = None
    font_size: Optional[int] = None
    show_word_count: Optional[bool] = None
    show_token_count: Optional[bool] = None
    default_prompt_type: Optional[str] = None

class Preference(BaseModel):
    """User preference."""
    key: str
    value: Any
    category: Optional[str] = None

class UserSettings(BaseModel):
    """User settings and preferences."""
    user_id: str
    llm_settings: LLMSettings = Field(default_factory=LLMSettings)
    ui_settings: UISettings = Field(default_factory=UISettings)
    preferences: List[Preference] = Field(default_factory=list)
    favorite_templates: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        Get a preference value.
        
        Args:
            key: Preference key
            default: Default value if not found
            
        Returns:
            Preference value or default
        """
        for pref in self.preferences:
            if pref.key == key:
                return pref.value
        return default
    
    def set_preference(self, key: str, value: Any, category: Optional[str] = None) -> None:
        """
        Set a preference value.
        
        Args:
            key: Preference key
            value: Preference value
            category: Preference category
        """
        # Check if preference already exists
        for pref in self.preferences:
            if pref.key == key:
                pref.value = value
                if category:
                    pref.category = category
                self.updated_at = datetime.utcnow()
                return
        
        # Add new preference
        self.preferences.append(Preference(key=key, value=value, category=category))
        self.updated_at = datetime.utcnow()
    
    def delete_preference(self, key: str) -> bool:
        """
        Delete a preference.
        
        Args:
            key: Preference key
            
        Returns:
            True if deleted, False if not found
        """
        for i, pref in enumerate(self.preferences):
            if pref.key == key:
                del self.preferences[i]
                self.updated_at = datetime.utcnow()
                return True
        return False
```

#### Create User Settings Storage

```
python# core/user_settings_storage.py
import json
import os
from datetime import datetime
from typing import Dict, Optional

from core.exceptions import SettingsError
from core.logging import get_logger
from core.user_settings import UserSettings

logger = get_logger(__name__)

class UserSettingsStorage:
    """
    Storage for user settings.
    
    Supports in-memory storage and file-based persistence.
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize the user settings storage.
        
        Args:
            storage_dir: Directory for file-based storage
        """
        self.settings: Dict[str, UserSettings] = {}
        self.storage_dir = storage_dir
        
        # Create storage directory if it doesn't exist
        if storage_dir and not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
            logger.info(f"Created user settings storage directory: {storage_dir}")
    
    def get_settings(self, user_id: str) -> UserSettings:
        """
        Get settings for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            User settings
        """
        if user_id not in self.settings:
            # Try to load from file
            if self.storage_dir:
                try:
                    self._load_settings(user_id)
                except Exception as e:
                    # Create new settings
                    self.settings[user_id] = UserSettings(user_id=user_id)
            else:
                # Create new settings
                self.settings[user_id] = UserSettings(user_id=user_id)
        
        return self.settings[user_id]
    
    def save_settings(self, settings: UserSettings) -> None:
        """
        Save settings for a user.
        
        Args:
            settings: User settings
        """
        # Update in memory
        self.settings[settings.user_id] = settings
        
        # Save to file
        self._save_settings(settings)
    
    def _save_settings(self, settings: UserSettings) -> None:
        """
        Save settings to file.
        
        Args:
            settings: User settings
        """
        if not self.storage_dir:
            return
        
        file_path = os.path.join(self.storage_dir, f"{settings.user_id}.json")
        
        try:
            # Convert to JSON-serializable dict
            data = settings.dict()
            
            # Convert datetime objects to strings
            data['created_at'] = data['created_at'].isoformat()
            data['updated_at'] = data['updated_at'].isoformat()
            
            # Write to file
            with open(file_path, 'w') as f:
                json.dump(data, f)
            
            logger.debug(f"Saved settings for user {settings.user_id}")
        except Exception as e:
            logger.error(f"Error saving settings for user {settings.user_id}: {str(e)}")
    
    def _load_settings(self, user_id: str) -> None:
        """
        Load settings from file.
        
        Args:
            user_id: User ID
            
        Raises:
            FileNotFoundError: If the settings file is not found
        """
        if not self.storage_dir:
            raise FileNotFoundError(f"Storage directory not configured")
        
        file_path = os.path.join(self.storage_dir, f"{user_id}.json")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Settings file not found: {file_path}")
        
        try:
            # Read from file
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Convert string timestamps to datetime
            data['created_at'] = datetime.fromisoformat(data['created_at'])
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
            
            # Create settings
            settings = UserSettings(**data)
            self.settings[user_id] = settings
            
            logger.debug(f"Loaded settings for user {user_id}")
        except Exception as e:
            logger.error(f"Error loading settings for user {user_id}: {str(e)}")
            raise
```

#### Create User Settings Endpoints

```
python# api/v1/routes.py
from flask import jsonify

from core.user_settings import LLMSettings, UISettings, Preference
from core.user_settings_storage import UserSettingsStorage

# Initialize user settings storage
user_settings_storage = UserSettingsStorage(
    storage_dir=current_app.config.get('USER_SETTINGS_STORAGE_DIR')
)

@api_v1.route('/settings', methods=['GET'])
@require_api_token
def get_user_settings():
    """
    Get settings for the user.
    
    Returns:
        User settings
    """
    user_id = request.headers.get('X-API-Token')
    settings = user_settings_storage.get_settings(user_id)
    
    return jsonify({
        'settings': {
            'llm_settings': settings.llm_settings.dict(),
            'ui_settings': settings.ui_settings.dict(),
            'preferences': [p.dict() for p in settings.preferences],
            'favorite_templates': settings.favorite_templates
        }
    })

@api_v1.route('/settings/llm', methods=['PUT'])
@require_api_token
def update_llm_settings():
    """
    Update LLM settings for the user.
    
    Returns:
        Updated LLM settings
    """
    user_id = request.headers.get('X-API-Token')
    settings = user_settings_storage.get_settings(user_id)
    
    # Update LLM settings
    llm_settings_data = request.json
    settings.llm_settings = LLMSettings(**llm_settings_data)
    settings.updated_at = datetime.utcnow()
    
    # Save settings
    user_settings_storage.save_settings(settings)
    
    return jsonify({
        'llm_settings': settings.llm_settings.dict()
    })

@api_v1.route('/settings/ui', methods=['PUT'])
@require_api_token
def update_ui_settings():
    """
    Update UI settings for the user.
    
    Returns:
        Updated UI settings
    """
    user_id = request.headers.get('X-API-Token')
    settings = user_settings_storage.get_settings(user_id)
    
    # Update UI settings
    ui_settings_data = request.json
    settings.ui_settings = UISettings(**ui_settings_data)
    settings.updated_at = datetime.utcnow()
    
    # Save settings
    user_settings_storage.save_settings(settings)
    
    return jsonify({
        'ui_settings': settings.ui_settings.dict()
    })

@api_v1.route('/settings/preferences', methods=['PUT'])
@require_api_token
def update_preference():
    """
    Set a preference for the user.
    
    Returns:
        Updated preference
    """
    user_id = request.headers.get('X-API-Token')
    settings = user_settings_storage.get_settings(user_id)
    
    # Get preference data
    key = request.json.get('key')
    value = request.json.get('value')
    category = request.json.get('category')
    
    if not key:
        return jsonify({
            'error': 'Invalid request',
            'details': 'Preference key is required',
            'code': 'INVALID_REQUEST'
        }), 400
    
    # Set preference
    settings.set_preference(key, value, category)
    
    # Save settings
    user_settings_storage.save_settings(settings)
    
    return jsonify({
        'preference': {
            'key': key,
            'value': value,
            'category': category
        }
    })

@api_v1.route('/settings/preferences/<key>', methods=['DELETE'])
@require_api_token
def delete_preference(key):
    """
    Delete a preference for the user.
    
    Returns:
        Success message
    """
    user_id = request.headers.get('X-API-Token')
    settings = user_settings_storage.get_settings(user_id)
    
    # Delete preference
    success = settings.delete_preference(key)
    
    # Save settings
    if success:
        user_settings_storage.save_settings(settings)
        return jsonify({
            'message': f'Preference {key} deleted successfully'
        })
    else:
        return jsonify({
            'error': 'Not found',
            'details': f'Preference {key} not found',
            'code': 'NOT_FOUND'
        }), 404

@api_v1.route('/settings/templates/favorites', methods=['PUT'])
@require_api_token
def update_favorite_templates():
    """
    Update favorite templates for the user.
    
    Returns:
        Updated favorite templates
    """
    user_id = request.headers.get('X-API-Token')
    settings = user_settings_storage.get_settings(user_id)
    
    # Get template IDs
    template_ids = request.json.get('template_ids', [])
    
    # Update favorite templates
    settings.favorite_templates = template_ids
    settings.updated_at = datetime.utcnow()
    
    # Save settings
    user_settings_storage.save_settings(settings)
    
    return jsonify({
        'favorite_templates': settings.favorite_templates
    })

@api_v1.route('/settings/templates/favorites/<template_id>', methods=['PUT'])
@require_api_token
def add_favorite_template(template_id):
    """
    Add a template to favorites.
    
    Returns:
        Updated favorite templates
    """
    user_id = request.headers.get('X-API-Token')
    settings = user_settings_storage.get_settings(user_id)
    
    # Add to favorites if not already there
    if template_id not in settings.favorite_templates:
        settings.favorite_templates.append(template_id)
        settings.updated_at = datetime.utcnow()
        
        # Save settings
        user_settings_storage.save_settings(settings)
    
    return jsonify({
        'favorite_templates': settings.favorite_templates
    })

@api_v1.route('/settings/templates/favorites/<template_id>', methods=['DELETE'])
@require_api_token
def remove_favorite_template(template_id):
    """
    Remove a template from favorites.
    
    Returns:
        Updated favorite templates
    """
    user_id = request.headers.get('X-API-Token')
    settings = user_settings_storage.get_settings(user_id)
    
    # Remove from favorites
    if template_id in settings.favorite_templates:
        settings.favorite_templates.remove(template_id)
        settings.updated_at = datetime.utcnow()
        
        # Save settings
        user_settings_storage.save_settings(settings)
    
    return jsonify({
        'favorite_templates': settings.favorite_templates
    })
```

#### Update Configuration for new components

```
python# core/config.py (additions)
class Settings(BaseSettings):
    """Application settings."""
    
    # Add new settings
    max_file_size_mb: int = Field(
        default=10, description="Maximum file size in MB"
    )
    templates_dir: Optional[str] = Field(
        default=None, description="Directory for prompt templates"
    )
    conversation_storage_dir: Optional[str] = Field(
        default=None, description="Directory for conversation storage"
    )
    user_settings_storage_dir: Optional[str] = Field(
        default=None, description="Directory for user settings storage"
    )
```

#### Update Exception Classes

```
python# core/exceptions.py (additions)
class TemplateError(APIError):
    """Error for template operations."""

    status_code = 400
    message = "Template operation failed"

class ConversationError(APIError):
    """Error for conversation operations."""

    status_code = 400
    message = "Conversation operation failed"

class FileProcessingError(APIError):
    """Error for file processing operations."""

    status_code = 400
    message = "File processing failed"

class SettingsError(APIError):
    """Error for settings operations."""

    status_code = 400
    message = "Settings operation failed"
```

## Example Templates for Different Use Cases

Let's create some example templates to demonstrate the template system:

```
json// templates/email_summary.json
{
  "id": "email_summary",
  "name": "Email Summary",
  "description": "Summarize an email and extract action items",
  "template": "Summarize the following email and extract any action items:\n\n{email_content}",
  "variables": [
    {
      "name": "email_content",
      "description": "The content of the email to summarize",
      "required": true
    }
  ],
  "system_prompt": "You are an assistant that helps summarize emails. Extract the key points and any action items or deadlines. Be concise and focus on what's important.",
  "type": "summary",
  "source": "email"
}
```

```
json// templates/meeting_notes.json
{
  "id": "meeting_notes",
  "name": "Meeting Notes",
  "description": "Process meeting notes and extract key decisions and action items",
  "template": "Process these meeting notes and extract the main discussion points, decisions made, and action items:\n\n{meeting_notes}",
  "variables": [
    {
      "name": "meeting_notes",
      "description": "The meeting notes to process",
      "required": true
    }
  ],
  "system_prompt": "You are an assistant that helps organize meeting notes. Extract the key discussion points, decisions made, and action items with assignees and deadlines if available. Present the information in a clear, structured format.",
  "type": "summary",
  "source": "meeting"
}
```

```
json// templates/technical_explanation.json
{
  "id": "technical_explanation",
  "name": "Technical Explanation",
  "description": "Explain a technical concept in simple terms",
  "template": "Explain {concept} in simple terms that {audience} can understand.",
  "variables": [
    {
      "name": "concept",
      "description": "The technical concept to explain",
      "required": true
    },
    {
      "name": "audience",
      "description": "The target audience",
      "required": true,
      "default": "a non-technical person"
    }
  ],
  "system_prompt": "You are an expert at explaining complex technical concepts in simple, accessible language. Use analogies, examples, and clear language to help people understand.",
  "type": "explanation",
  "source": "other"
}
```

## Requirements Update

We need to add several new dependencies to support these features:

```
# Add to requirements.txt

# File processing
PyMuPDF==1.23.8       # For PDF processing
python-docx==1.0.1    # For DOCX processing
pytesseract==0.3.10   # For OCR
pillow==10.2.0        # For image processing
pandas==2.1.4         # For CSV/Excel processing
openpyxl==3.1.2       # For Excel processing

# Streaming responses
werkzeug==3.0.1       # Flask dependency that supports streaming

# Type hints
typing-extensions==4.9.0
```

## Enhanced Features Documentation

Here's a documentation page for the new features:

```
markdown# FlaskLLM API: Enhanced Features

The FlaskLLM API includes several advanced features that extend its capabilities and improve the user experience. This document describes these features and provides examples of how to use them.

## Table of Contents
1. [Streaming Responses](#streaming-responses)
2. [Prompt Templates](#prompt-templates)
3. [Custom LLM Parameters](#custom-llm-parameters)
4. [File Processing](#file-processing)
5. [Conversation History](#conversation-history)
6. [User-Specific Customizations](#user-specific-customizations)

## Streaming Responses

Streaming responses allow the API to send partial results as they become available, providing a more responsive user experience for longer generations.

### Endpoint
```

POST /api/v1/stream

```

### Request

```json
{
  "prompt": "Write a detailed explanation of how neural networks learn",
  "source": "other",
  "language": "en",
  "type": "explanation",
  "parameters": {
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

### Response

The response is a server-sent events (SSE) stream with the following format:

```
data: {"chunk": "Neural networks learn through"}
data: {"chunk": " a process called backpropagation."}
...
data: [DONE]
```

### Client-Side Integration

Here's an example of how to consume the streaming response in JavaScript:

```
javascriptconst apiUrl = 'https://yourusername.pythonanywhere.com/api/v1/stream';
const apiToken = 'your_api_token';

const body = JSON.stringify({
  prompt: 'Write a detailed explanation of how neural networks learn',
  source: 'other',
  language: 'en',
  type: 'explanation'
});

// Create event source
const eventSource = new EventSource(`${apiUrl}?api_token=${apiToken}`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: body
});

let fullResponse = '';

// Handle incoming chunks
eventSource.onmessage = (event) => {
  if (event.data === '[DONE]') {
    // Stream complete
    eventSource.close();
    console.log('Full response:', fullResponse);
    return;
  }
  
  const data = JSON.parse(event.data);
  if (data.chunk) {
    fullResponse += data.chunk;
    console.log('Received chunk:', data.chunk);
    // Update UI with new content
    document.getElementById('response').innerText = fullResponse;
  }
};

// Handle errors
eventSource.onerror = (error) => {
  console.error('Stream error:', error);
  eventSource.close();
};
```

## Prompt Templates

Prompt templates allow reusing common patterns and including custom variables, making it easier to create consistent prompts for different use cases.

### Managing Templates

#### List Templates

#### Get Template

```
GET /api/v1/templates/{template_id}
```

#### Create Template

Request body:

```
json{
  "id": "email_summary",
  "name": "Email Summary",
  "description": "Summarize an email and extract action items",
  "template": "Summarize the following email and extract any action items:\n\n{email_content}",
  "variables": [
    {
      "name": "email_content",
      "description": "The content of the email to summarize",
      "required": true
    }
  ],
  "system_prompt": "You are an assistant that helps summarize emails. Extract the key points and any action items or deadlines. Be concise and focus on what's important.",
  "type": "summary",
  "source": "email"
}
```

#### Update Template

```
PUT /api/v1/templates/{template_id}
```

#### Delete Template

```
DELETE /api/v1/templates/{template_id}
```

### Using Templates

#### Render Template

```
POST /api/v1/templates/{template_id}/render
```

Request body:

```
json{
  "variables": {
    "email_content": "Dear Team,\n\nWe need to submit the quarterly report by Friday. Please send me your sections by Wednesday.\n\nRegards,\nManager"
  }
}
```

#### Process Template

```
POST /api/v1/templates/{template_id}/process
```

Request body:

```
json{
  "variables": {
    "email_content": "Dear Team,\n\nWe need to submit the quarterly report by Friday. Please send me your sections by Wednesday.\n\nRegards,\nManager"
  },
  "parameters": {
    "temperature": 0.3,
    "max_tokens": 200
  }
}
```

## Custom LLM Parameters

The API supports passing custom parameters to the LLM provider, allowing fine-tuned control over generation.

### Supported Parameters

-   `temperature`: Controls randomness (0.0 to 1.0)
-   `max_tokens`: Maximum number of tokens to generate
-   `top_p`: Nucleus sampling parameter (0.0 to 1.0)
-   `frequency_penalty`: Penalty for token frequency (-2.0 to 2.0)
-   `presence_penalty`: Penalty for token presence (-2.0 to 2.0)
-   `stop`: List of strings to stop generation

### Example

Request body:

```
json{
  "prompt": "Write a creative story about a space explorer",
  "source": "other",
  "type": "creative",
  "parameters": {
    "temperature": 0.8,
    "max_tokens": 500,
    "frequency_penalty": 0.5
  }
}
```

## File Processing

The API supports processing various file types, including PDF, DOCX, CSV, and images.

### Upload and Process Files

#### Upload File

```
POST /api/v1/files/upload
```

This endpoint expects a `multipart/form-data` request with a file in the `file` field.

#### Process File with LLM

```
POST /api/v1/files/process
```

This endpoint expects a `multipart/form-data` request with:

-   `file`: The file to process
-   `prompt_prefix`: Custom prompt prefix (e.g., "Summarize the following content:")
-   `max_tokens`: Maximum tokens to generate for the response

### Supported File Types

-   PDF (`.pdf`)
-   Word documents (`.docx`)
-   Text files (`.txt`)
-   CSV files (`.csv`)
-   Excel files (`.xlsx`, `.xls`)
-   Images (`.jpg`, `.jpeg`, `.png`) - with OCR for text extraction

## Conversation History

The API supports maintaining conversation history across multiple interactions, enabling stateful conversations.

### Managing Conversations

#### List Conversations

```
GET /api/v1/conversations
```

#### Create Conversation

```
POST /api/v1/conversations
```

Request body:

```
json{
  "title": "Technical Support Chat",
  "system_prompt": "You are a technical support assistant. Help the user solve their technical issues.",
  "metadata": {
    "category": "support",
    "priority": "high"
  }
}
```

#### Get Conversation

```
GET /api/v1/conversations/{conversation_id}
```

#### Delete Conversation

```
DELETE /api/v1/conversations/{conversation_id}
```

### Adding Messages

```
POST /api/v1/conversations/{conversation_id}/messages
```

Request body:

```
json{
  "content": "I'm having trouble connecting to the internet",
  "stream": false
}
```

For streaming responses, set `stream` to `true`.

## User-Specific Customizations

The API supports storing and retrieving user-specific settings and preferences.

### Managing Settings

#### Get User Settings

#### Update LLM Settings

Request body:

```
json{
  "provider": "openai",
  "model": "gpt-4",
  "temperature": 0.5,
  "max_tokens": 1000,
  "system_prompt": "You are a helpful assistant."
}
```

#### Update UI Settings

Request body:

```
json{
  "theme": "dark",
  "font_size": 14,
  "show_word_count": true,
  "show_token_count": true,
  "default_prompt_type": "summary"
}
```

### Managing Preferences

#### Set Preference

```
PUT /api/v1/settings/preferences
```

Request body:

```
json{
  "key": "notification_email",
  "value": "user@example.com",
  "category": "notifications"
}
```

#### Delete Preference

```
DELETE /api/v1/settings/preferences/{key}
```

### Managing Favorite Templates

#### Update Favorite Templates

```
PUT /api/v1/settings/templates/favorites
```

Request body:

```
json{
  "template_ids": ["email_summary", "meeting_notes"]
}
```

#### Add Template to Favorites

```
PUT /api/v1/settings/templates/favorites/{template_id}
```

#### Remove Template from Favorites

```
DELETE /api/v1/settings/templates/favorites/{template_id}
```

```

## Testing

To test these new features, we can create test cases for each component. Here's an example for testing templates:

```python
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
```
