# flaskllm/api/v1/routes.py
"""
API Routes Module

This module defines the routes for the API endpoints.
"""
import time
from typing import Dict, Any

from flask import Response, current_app, request
from flask_restx import Api, Resource, fields

from flaskllm.api.v1.schemas import PromptRequest, PromptResponse, PromptSource, PromptType, validate_request
from flaskllm.core.auth import auth_required
from flaskllm.core.exceptions import InvalidInputError, APIError
from flaskllm.core.logging import get_logger
from flaskllm.llm.factory import get_llm_handler

# Configure logger
logger = get_logger(__name__)


def register_routes(api: Api) -> None:
    """
    Register routes with the given API.

    Args:
        api: Flask-RESTX API instance
    """
    # Define Namespace
    ns = api.namespace('', description='FlaskLLM API Operations')
    
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
        }))
        def get(self) -> Dict[str, Any]:
            """Health check endpoint."""
            return {
                "status": "ok",
                "version": "1.0.0",
                "environment": current_app.config["SETTINGS"].environment,
            }
    
    # Process prompt endpoint
    @ns.route('/webhook')
    class ProcessPrompt(Resource):
        @ns.doc(description='Process a prompt with the configured LLM provider', security='apikey')
        @ns.expect(prompt_request_model)
        @ns.response(200, 'Success', prompt_response_model)
        @ns.response(400, 'Invalid input data', error_model)
        @ns.response(401, 'Authentication failed', error_model)
        @ns.response(429, 'Rate limit exceeded', error_model)
        @ns.response(500, 'Internal server error', error_model)
        @ns.response(502, 'LLM API error', error_model)
        @auth_required
        def post(self) -> Dict[str, Any]:
            """Process a prompt with the configured LLM provider."""
            # Validate request body
            try:
                data = request.get_json()
                if not data:
                    raise InvalidInputError("Request body is required")

                # Validate with schema
                prompt_request = validate_request(PromptRequest, data)
            except ValueError as e:
                logger.warning("Invalid request data", error=str(e))
                raise InvalidInputError(str(e))

            # Process the prompt
            start_time = time.time()

            settings = current_app.config["SETTINGS"]
            llm_handler = get_llm_handler(settings)

            try:
                result = llm_handler.process_prompt(
                    prompt=prompt_request.prompt,
                    source=prompt_request.source,
                    language=prompt_request.language,
                    type=prompt_request.type,
                )
            except Exception as e:
                logger.error("Error processing prompt", error=str(e))
                raise

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

            # Return response
            return {
                "summary": result, 
                "processing_time": round(processing_time, 2)
            }