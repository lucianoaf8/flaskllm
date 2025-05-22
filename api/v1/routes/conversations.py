"""
Conversation API Routes

This module provides API routes for conversation management, including:
- Creating and retrieving conversations
- Adding messages to conversations
- Listing user conversations
- Deleting conversations
"""
from flask import Blueprint, Response, current_app, jsonify, request
from api.v1.schemas.conversations import ConversationRequest, ConversationResponse
from core.auth import auth_required
from llm.storage.conversations import ConversationStorage

# Create a blueprint for the conversation routes
bp = Blueprint('conversations', __name__, url_prefix='/conversations')

# Initialize logger
from core.logging import get_logger
logger = get_logger(__name__)

@bp.route('/', methods=['POST'])
@auth_required
def create_conversation():
    """
    Create a new conversation.

    Returns:
        Created conversation data
    """
    try:
        # Parse request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
            
        # Get user ID from authentication
        user_id = request.headers.get('X-API-Token')
        
        # Get conversation parameters
        title = data.get('title')
        system_prompt = data.get('system_prompt')
        metadata = data.get('metadata', {})
        
        # Get conversation storage
        storage = ConversationStorage()
        
        # Create conversation
        conversation = storage.create_conversation(
            user_id=user_id,
            title=title,
            system_prompt=system_prompt,
            metadata=metadata
        )
        
        # Return created conversation
        return jsonify({
            "conversation": conversation.dict()
        }), 201
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/<conversation_id>', methods=['GET'])
@auth_required
def get_conversation(conversation_id):
    """
    Get a conversation by ID.

    Args:
        conversation_id: Conversation ID

    Returns:
        Conversation data
    """
    try:
        # Get conversation storage
        storage = ConversationStorage()
        
        # Get conversation
        conversation = storage.get_conversation(conversation_id)
        
        # Return conversation
        return jsonify({
            "conversation": conversation.dict()
        }), 200
    except Exception as e:
        logger.error(f"Error getting conversation {conversation_id}: {str(e)}")
        return jsonify({"error": str(e)}), 404

@bp.route('/<conversation_id>/messages', methods=['POST'])
@auth_required
def add_message(conversation_id):
    """
    Add a message to a conversation.

    Args:
        conversation_id: Conversation ID

    Returns:
        Added message data
    """
    try:
        # Parse request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
            
        # Get message parameters
        role = data.get('role')
        if not role:
            return jsonify({"error": "Message role is required"}), 400
            
        content = data.get('content')
        if not content:
            return jsonify({"error": "Message content is required"}), 400
        
        # Get conversation storage
        storage = ConversationStorage()
        
        # Add message
        from llm.conversation import MessageRole
        try:
            role_enum = MessageRole(role)
        except ValueError:
            return jsonify({"error": f"Invalid role: {role}. Must be one of: {', '.join([r.value for r in MessageRole])}"}), 400
            
        message = storage.add_message(
            conversation_id=conversation_id,
            role=role_enum,
            content=content
        )
        
        # Return added message
        return jsonify({
            "message": message.dict()
        }), 201
    except Exception as e:
        logger.error(f"Error adding message to conversation {conversation_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/user/<user_id>', methods=['GET'])
@auth_required
def list_conversations(user_id):
    """
    List conversations for a user.

    Args:
        user_id: User ID

    Returns:
        List of conversation summaries
    """
    try:
        # Get conversation storage
        storage = ConversationStorage()
        
        # List conversations
        conversations = storage.list_conversations(user_id)
        
        # Return conversations
        return jsonify({
            "conversations": [conv.dict() for conv in conversations]
        }), 200
    except Exception as e:
        logger.error(f"Error listing conversations for user {user_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/<conversation_id>', methods=['DELETE'])
@auth_required
def delete_conversation(conversation_id):
    """
    Delete a conversation.

    Args:
        conversation_id: Conversation ID

    Returns:
        Success message
    """
    try:
        # Get conversation storage
        storage = ConversationStorage()
        
        # Delete conversation
        deleted = storage.delete_conversation(conversation_id)
        
        if deleted:
            return jsonify({
                "message": f"Conversation {conversation_id} deleted"
            }), 200
        else:
            return jsonify({
                "error": f"Conversation {conversation_id} not found"
            }), 404
    except Exception as e:
        logger.error(f"Error deleting conversation {conversation_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500
