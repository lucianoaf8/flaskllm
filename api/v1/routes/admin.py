"""
Admin API Routes

This module provides administrative API routes for the application, including:
- User settings management
- Usage examples
- Application settings
"""
from datetime import datetime
from flask import Blueprint, Response, current_app, jsonify, request
from api.v1.schemas.auth import UserSettingsRequest
from core.auth import auth_required
from core.settings.models import UserSettings

# Create a blueprint for the admin routes
bp = Blueprint('admin', __name__, url_prefix='/admin')

# Initialize logger
from core.logging import get_logger
logger = get_logger(__name__)

# Initialize user settings storage
from core.settings.storage import UserSettingsStorage
from core.settings.models import LLMSettings, UISettings, Preference

# User Settings routes
@bp.route('/settings', methods=['GET'])
@auth_required
def get_user_settings():
    """
    Get settings for the user.

    Returns:
        User settings
    """
    # Initialize user settings storage
    user_settings_storage = UserSettingsStorage(
        storage_dir=current_app.config.get("SETTINGS").user_settings_storage_dir
    )
    
    user_id = request.headers.get('X-API-Token')
    settings = user_settings_storage.get_settings(user_id)

    return jsonify({
        'settings': {
            'llm_settings': settings.llm_settings.dict(),
            'ui_settings': settings.ui_settings.dict(),
            'preferences': [p.dict() for p in settings.preferences],
            'favorite_templates': settings.favorite_templates
        }
    }), 200

@bp.route('/settings/llm', methods=['PUT'])
@auth_required
def update_llm_settings():
    """
    Update LLM settings for the user.

    Returns:
        Updated LLM settings
    """
    # Initialize user settings storage
    user_settings_storage = UserSettingsStorage(
        storage_dir=current_app.config.get("SETTINGS").user_settings_storage_dir
    )
    
    user_id = request.headers.get('X-API-Token')
    settings = user_settings_storage.get_settings(user_id)

    # Update LLM settings
    llm_settings_data = request.get_json()
    settings.llm_settings = LLMSettings(**llm_settings_data)
    settings.updated_at = datetime.utcnow()

    # Save settings
    user_settings_storage.save_settings(settings)

    return jsonify({
        'llm_settings': settings.llm_settings.dict()
    }), 200

@bp.route('/settings/ui', methods=['PUT'])
@auth_required
def update_ui_settings():
    """
    Update UI settings for the user.

    Returns:
        Updated UI settings
    """
    # Initialize user settings storage
    user_settings_storage = UserSettingsStorage(
        storage_dir=current_app.config.get("SETTINGS").user_settings_storage_dir
    )
    
    user_id = request.headers.get('X-API-Token')
    settings = user_settings_storage.get_settings(user_id)

    # Update UI settings
    ui_settings_data = request.get_json()
    settings.ui_settings = UISettings(**ui_settings_data)
    settings.updated_at = datetime.utcnow()

    # Save settings
    user_settings_storage.save_settings(settings)

    return jsonify({
        'ui_settings': settings.ui_settings.dict()
    }), 200

@bp.route('/settings/preferences', methods=['PUT'])
@auth_required
def update_preference():
    """
    Set a preference for the user.

    Returns:
        Updated preference
    """
    # Initialize user settings storage
    user_settings_storage = UserSettingsStorage(
        storage_dir=current_app.config.get("SETTINGS").user_settings_storage_dir
    )
    
    user_id = request.headers.get('X-API-Token')
    settings = user_settings_storage.get_settings(user_id)

    # Get preference data
    data = request.get_json()
    key = data.get('key')
    value = data.get('value')
    category = data.get('category')

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
    }), 200

@bp.route('/settings/preferences/<key>', methods=['DELETE'])
@auth_required
def delete_preference(key):
    """
    Delete a preference for the user.

    Returns:
        Success message
    """
    # Initialize user settings storage
    user_settings_storage = UserSettingsStorage(
        storage_dir=current_app.config.get("SETTINGS").user_settings_storage_dir
    )
    
    user_id = request.headers.get('X-API-Token')
    settings = user_settings_storage.get_settings(user_id)

    # Delete preference
    success = settings.delete_preference(key)

    # Save settings
    if success:
        user_settings_storage.save_settings(settings)
        return jsonify({
            'message': f'Preference {key} deleted successfully'
        }), 200
    else:
        return jsonify({
            'error': 'Not found',
            'details': f'Preference {key} not found',
            'code': 'NOT_FOUND'
        }), 404

@bp.route('/settings/templates/favorites', methods=['PUT'])
@auth_required
def update_favorite_templates():
    """
    Update favorite templates for the user.

    Returns:
        Updated favorite templates
    """
    # Initialize user settings storage
    user_settings_storage = UserSettingsStorage(
        storage_dir=current_app.config.get("SETTINGS").user_settings_storage_dir
    )
    
    user_id = request.headers.get('X-API-Token')
    settings = user_settings_storage.get_settings(user_id)

    # Get template IDs
    data = request.get_json()
    template_ids = data.get('template_ids', [])

    # Update favorite templates
    settings.favorite_templates = template_ids
    settings.updated_at = datetime.utcnow()

    # Save settings
    user_settings_storage.save_settings(settings)

    return jsonify({
        'favorite_templates': settings.favorite_templates
    }), 200

@bp.route('/settings/templates/favorites/<template_id>', methods=['PUT'])
@auth_required
def add_favorite_template(template_id):
    """
    Add a template to favorites.

    Returns:
        Updated favorite templates
    """
    # Initialize user settings storage
    user_settings_storage = UserSettingsStorage(
        storage_dir=current_app.config.get("SETTINGS").user_settings_storage_dir
    )
    
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
    }), 200

@bp.route('/settings/templates/favorites/<template_id>', methods=['DELETE'])
@auth_required
def remove_favorite_template(template_id):
    """
    Remove a template from favorites.

    Returns:
        Updated favorite templates
    """
    # Initialize user settings storage
    user_settings_storage = UserSettingsStorage(
        storage_dir=current_app.config.get("SETTINGS").user_settings_storage_dir
    )
    
    user_id = request.headers.get('X-API-Token')
    settings = user_settings_storage.get_settings(user_id)

    # Remove from favorites if present
    if template_id in settings.favorite_templates:
        settings.favorite_templates.remove(template_id)
        settings.updated_at = datetime.utcnow()

        # Save settings
        user_settings_storage.save_settings(settings)

    return jsonify({
        'favorite_templates': settings.favorite_templates
    }), 200

# Examples routes
@bp.route('/examples', methods=['GET'])
@auth_required
def get_examples():
    """Get examples of how to use the API"""
    return jsonify({
        'examples': [
            {
                'name': 'Process email summary',
                'description': 'Extract key information from an email',
                'request': {
                    'method': 'POST',
                    'url': '/api/v1/core/webhook',
                    'headers': {
                        'Content-Type': 'application/json',
                        'X-API-Token': '[your-api-token]'
                    },
                    'body': {
                        'prompt': 'Please summarize this email: We need to schedule a meeting to discuss Q3 results.',
                        'source': 'email',
                        'type': 'summary'
                    }
                },
                'response': {
                    'result': 'A meeting needs to be scheduled to discuss Q3 results.',
                    'processing_time': 1.25
                }
            },
            {
                'name': 'Upload and process file',
                'description': 'Upload a file and process its contents with LLM',
                'request': {
                    'method': 'POST',
                    'url': '/api/v1/files/process',
                    'headers': {
                        'X-API-Token': '[your-api-token]'
                    },
                    'body': {
                        'form-data': {
                            'file': '(binary file content)',
                            'prompt_prefix': 'Summarize the key points from this document:'
                        }
                    }
                },
                'response': {
                    'result': 'The document discusses the quarterly financial results...',
                    'metadata': {
                        'filename': 'report.pdf',
                        'file_type': 'pdf',
                        'size_bytes': 125000,
                        'page_count': 5
                    }
                }
            }
        ]
    }), 200
