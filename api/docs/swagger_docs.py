# api/v1/routes.py
from flask import request, current_app
from flask_restx import Resource, fields

from . import api
from .schemas import PromptSchema, ResponseSchema
from core.auth import require_api_token
from llm.factory import get_llm_handler
from utils.rate_limiter import rate_limit

# Define models for Swagger documentation
prompt_model = api.model('Prompt', {
    'prompt': fields.String(required=True, description='The text to process', example='Summarize this meeting: we need to reduce hiring.'),
    'source': fields.String(required=False, description='Source of the prompt', enum=['email', 'meeting', 'document', 'chat', 'other'], example='meeting'),
    'language': fields.String(required=False, description='Target language code (ISO 639-1)', example='en'),
    'type': fields.String(required=False, description='Type of processing', enum=['summary', 'keywords', 'sentiment', 'entities', 'translation', 'custom'], example='summary')
})

response_model = api.model('Response', {
    'summary': fields.String(description='Processed response from LLM', example='The company plans to reduce hiring to cut costs.'),
    'processing_time': fields.Float(description='Time taken to process the request in seconds', example=1.25)
})

error_model = api.model('Error', {
    'error': fields.String(description='Error message'),
    'details': fields.String(description='Detailed explanation'),
    'code': fields.String(description='Error code')
})

# Register namespace
webhook_ns = api.namespace('webhook', description='Process prompts with LLM')

@webhook_ns.route('')
class Webhook(Resource):
    @webhook_ns.doc(security='apikey')
    @webhook_ns.expect(prompt_model)
    @webhook_ns.response(200, 'Success', response_model)
    @webhook_ns.response(400, 'Validation Error', error_model)
    @webhook_ns.response(401, 'Authentication Error', error_model)
    @webhook_ns.response(429, 'Rate Limit Exceeded', error_model)
    @webhook_ns.response(500, 'Server Error', error_model)
    @webhook_ns.response(502, 'LLM API Error', error_model)
    @require_api_token
    @rate_limit
    def post(self):
        """Process a prompt with the configured LLM provider"""
        start_time = time.time()

        # Validate input
        try:
            schema = PromptSchema()
            data = schema.load(request.json)
        except ValidationError as e:
            return {
                'error': 'Validation Error',
                'details': str(e),
                'code': 'VALIDATION_ERROR'
            }, 400

        # Process the prompt
        try:
            llm_handler = get_llm_handler()
            result = llm_handler.process_prompt(
                data['prompt'],
                data.get('source'),
                data.get('language'),
                data.get('type')
            )

            # Calculate processing time
            processing_time = time.time() - start_time

            # Return result
            return {
                'summary': result,
                'processing_time': round(processing_time, 2)
            }
        except Exception as e:
            current_app.logger.error(f"Error processing prompt: {str(e)}", exc_info=True)
            return {
                'error': 'LLM API Error',
                'details': str(e),
                'code': 'LLM_API_ERROR'
            }, 502
