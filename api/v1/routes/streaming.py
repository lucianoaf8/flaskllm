"""
Streaming API Routes

This module provides API routes for streaming LLM responses, which is useful for
real-time applications where parts of the response should be displayed incrementally.
"""
import json
from flask import Blueprint, Response, current_app, jsonify, request, stream_with_context
from api.v1.schemas.common import StreamingRequest
from core.auth import auth_required
from llm.handlers.openai import OpenAIHandler

# Create a blueprint for the streaming routes
bp = Blueprint('streaming', __name__, url_prefix='/stream')

# Initialize logger
from core.logging import get_logger
logger = get_logger(__name__)

@bp.route('/', methods=['POST'])
@auth_required
def stream_prompt():
    """
    Process a prompt with the configured LLM provider and stream the response.

    Returns:
        Streamed response from LLM
    """
    # Validate input
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
            
        streaming_request = StreamingRequest(**data)
        
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        return jsonify({
            'error': 'Validation Error',
            'details': str(e),
            'code': 'VALIDATION_ERROR'
        }), 400

    try:
        # Get custom parameters
        custom_params = {}
        if hasattr(streaming_request, 'max_tokens') and streaming_request.max_tokens:
            custom_params['max_tokens'] = streaming_request.max_tokens
        if hasattr(streaming_request, 'temperature') and streaming_request.temperature:
            custom_params['temperature'] = streaming_request.temperature

        # Get LLM handler
        from llm.factory import get_llm_handler
        llm_handler = get_llm_handler(current_app.config.get("SETTINGS"))

        # Start the streaming response
        def generate():
            try:
                # Process the prompt with streaming enabled
                for chunk in llm_handler.process_prompt(
                    prompt=streaming_request.prompt,
                    stream=True,
                    **custom_params
                ):
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            except Exception as e:
                logger.error(f"Streaming error: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

            # End the stream
            yield "data: [DONE]\n\n"

        # Return the streamed response
        return Response(
            stream_with_context(generate()),
            content_type='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'  # Disable buffering in Nginx
            }
        )
    except Exception as e:
        logger.error(f"Error processing prompt: {str(e)}")
        return jsonify({
            'error': 'LLM API Error',
            'details': str(e),
            'code': 'LLM_API_ERROR'
        }), 502
