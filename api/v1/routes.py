# flaskllm/api/v1/routes.py
"""
API Routes Module

This module defines and registers the routes for the v1 API endpoints. It configures
the Flask-RESTX resources, input/output models, and authentication requirements.

The main endpoints include:
- /health: Health check endpoint to verify API status
- /webhook: Main prompt processing endpoint for LLM interactions

Additional endpoints (user settings, file uploads, conversations) are registered
from their respective modules.
"""
import time
import sys
from typing import Dict, Any, Tuple, Optional

from flask import Response, current_app, request, jsonify
from flask_restx import Api, Resource, fields

from api.v1.schemas import PromptRequest, PromptResponse, PromptSource, PromptType, validate_request
from core.auth import auth_required
from core.exceptions import InvalidInputError, APIError
from core.logging import get_logger
from llm.factory import get_llm_handler

# Configure logger
logger = get_logger(__name__)


def register_routes(api: Api) -> None:
    """
    Register all v1 API routes with the given API instance.
    
    This function defines and registers the core API endpoints and imports
    additional route modules to register their endpoints as well.

    Args:
        api: Flask-RESTX API instance
        
    Raises:
        ImportError: If a required route module cannot be imported
    """
    # Define Namespace
    ns = api.namespace('', description='FlaskLLM API Operations')
    
    # Try to register routes from other modules
    try:
        # Import route modules
        from api.v1.health_check import register_health_routes
        from api.v1.user_settings_routes import register_settings_routes
        from api.v1.file_routes import register_file_routes
        from api.v1.conversation_routes import register_conversation_routes
        
        # Register routes from each module
        logger.info("Registering additional route modules")
        
        # These functions should be implemented in each module
        # If they're not yet implemented, the imports will still succeed
        # but the function calls will be skipped with a warning
        
        # Try to register each module's routes
        try:
            register_health_routes(api, ns)
            logger.debug("Registered health routes")
        except (AttributeError, TypeError):
            logger.warning("Health routes registration function not implemented correctly")
            
        try:
            register_settings_routes(api, ns)
            logger.debug("Registered user settings routes")
        except (AttributeError, TypeError):
            logger.warning("Settings routes registration function not implemented correctly")
            
        try:
            register_file_routes(api, ns)
            logger.debug("Registered file routes")
        except (AttributeError, TypeError):
            logger.warning("File routes registration function not implemented correctly")
            
        try:
            register_conversation_routes(api, ns)
            logger.debug("Registered conversation routes")
        except (AttributeError, TypeError):
            logger.warning("Conversation routes registration function not implemented correctly")
            
    except ImportError as e:
        # Log the error but continue with core routes
        logger.warning(f"Could not import additional route modules: {str(e)}")
    
    # Define Models for Swagger documentation
    prompt_source_enum = list(PromptSource.__members__.keys())
    prompt_type_enum = list(PromptType.__members__.keys())
    
    # Request model
    prompt_request_model = api.model('PromptRequest', {
        'prompt': fields.String(required=True, description='The text to process', example='Summarize this meeting: we need to reduce hiring.'),
        'source': fields.String(required=False, description='Source of the prompt', enum=prompt_source_enum, default='OTHER', example='meeting'),
        'language': fields.String(required=False, description='Target language code (ISO 639-1)', example='en'),
        'type': fields.String(required=False, description='Type of processing to perform', enum=prompt_type_enum, default='SUMMARY', example='summary'),
    })
    
    # Response model
    prompt_response_model = api.model('PromptResponse', {
        'summary': fields.String(description='Processed result from LLM', example='The company plans to reduce hiring to cut costs.'),
        'processing_time': fields.Float(description='Processing time in seconds', example=1.25),
    })
    
    # Error model
    error_model = api.model('ErrorResponse', {
        'error': fields.String(description='Error message'),
    })
    
    # Health check endpoint
    @ns.route('/health')
    class HealthCheck(Resource):
        @ns.doc(description='Health check endpoint')
        @ns.response(200, 'Success', api.model('HealthResponse', {
            'status': fields.String(description='API status', example='ok'),
            'version': fields.String(description='API version', example='1.0.0'),
            'environment': fields.String(description='Current environment', example='production'),
            'python_version': fields.String(description='Python version', example='3.10.4'),
            'system_info': fields.Raw(description='System information'),
        }))
        def get(self) -> Tuple[Dict[str, Any], int]:
            """Health check endpoint that returns API status information."""
            # Get settings from app config
            settings = current_app.config.get("SETTINGS")
            if not settings:
                logger.error("Settings not found in app config")
                return {"status": "error", "error": "Configuration missing"}, 500
                
            # Get API version from the API instance if available
            api_version = getattr(api, 'version', '1.0.0')
            
            # Prepare response
            response = {
                "status": "ok",
                "version": api_version,
                "environment": settings.environment,
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "system_info": {
                    "llm_provider": settings.llm_provider,
                    "debug_mode": settings.debug,
                    "rate_limiting": settings.rate_limit_enabled,
                }
            }
            
            # Check if LLM provider is configured
            try:
                # Lightweight check - just verify we can create the handler
                _ = get_llm_handler(settings)
                response["system_info"]["llm_status"] = "configured"
            except Exception as e:
                logger.warning("LLM provider not properly configured", error=str(e))
                response["system_info"]["llm_status"] = "error"
                response["system_info"]["llm_error"] = str(e)
                
            return response, 200
    
    # Process prompt endpoint
    @ns.route('/webhook')
    class ProcessPrompt(Resource):
        """Resource for processing prompts with the LLM provider."""
        
        @ns.doc(description='Process a prompt with the configured LLM provider', security='apikey')
        @ns.expect(prompt_request_model)
        @ns.response(200, 'Success', prompt_response_model)
        @ns.response(400, 'Invalid input data', error_model)
        @ns.response(401, 'Authentication failed', error_model)
        @ns.response(429, 'Rate limit exceeded', error_model)
        @ns.response(500, 'Internal server error', error_model)
        @ns.response(502, 'LLM API error', error_model)
        @auth_required
        def post(self) -> Tuple[Dict[str, Any], int]:
            """Process a prompt with the configured LLM provider."""
            # Validate request body
            try:
                data = request.get_json()
                if not data:
                    logger.warning("Empty request received")
                    raise InvalidInputError("Request body is required")

                # Validate with schema
                prompt_request = validate_request(PromptRequest, data)
                
                # Log request information (without full prompt content for privacy)
                logger.info(
                    "Received prompt request", 
                    prompt_length=len(prompt_request.prompt),
                    source=prompt_request.source,
                    language=prompt_request.language,
                    type=prompt_request.type
                )
            except ValueError as e:
                logger.warning("Invalid request data", error=str(e))
                raise InvalidInputError(str(e))
            except Exception as e:
                logger.error("Unexpected error during request validation", error=str(e))
                raise APIError(f"Failed to process request: {str(e)}", status_code=500)

            # Process the prompt
            start_time = time.time()

            try:
                # Get settings and LLM handler
                settings = current_app.config.get("SETTINGS")
                if not settings:
                    raise APIError("Application configuration missing", status_code=500)
                    
                llm_handler = get_llm_handler(settings)

                # Process the prompt with the LLM
                result = llm_handler.process_prompt(
                    prompt=prompt_request.prompt,
                    source=prompt_request.source,
                    language=prompt_request.language,
                    type=prompt_request.type,
                )
            except APIError as e:
                # Re-raise existing API errors
                logger.error(
                    "API error processing prompt", 
                    error_type=e.__class__.__name__,
                    error=str(e),
                    status_code=e.status_code
                )
                raise
            except Exception as e:
                # Wrap other exceptions as API errors
                logger.error(
                    "Unexpected error processing prompt", 
                    error_type=e.__class__.__name__,
                    error=str(e)
                )
                raise APIError(f"Error processing prompt: {str(e)}", status_code=500)

            # Calculate processing time
            processing_time = time.time() - start_time

            # Log successful processing
            logger.info(
                "Prompt processed successfully",
                prompt_length=len(prompt_request.prompt),
                source=prompt_request.source,
                language=prompt_request.language,
                type=prompt_request.type,
                processing_time=f"{processing_time:.2f}s",
            )

            # Return response in the format specified by project guidelines
            response = {
                "data": {
                    "summary": result,
                    "processing_time": round(processing_time, 2)
                },
                "meta": {
                    "prompt_length": len(prompt_request.prompt),
                    "source": prompt_request.source,
                    "language": prompt_request.language,
                    "type": prompt_request.type
                }
            }
            
            return response, 200