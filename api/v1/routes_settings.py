# api/v1/routes.py
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
