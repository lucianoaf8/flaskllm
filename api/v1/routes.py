# flaskllm/api/v1/routes.py
"""
API Routes Module

This module defines the routes for the API endpoints.
"""
import time

from flask import Blueprint, Response, current_app, jsonify, request

from api.v1.schemas import PromptRequest, validate_request
from core.auth import auth_required
from core.exceptions import InvalidInputError
from core.logging import get_logger
from llm.factory import get_llm_handler

# Configure logger
logger = get_logger(__name__)


def register_routes(bp: Blueprint) -> None:
    """
    Register routes with the given blueprint.

    Args:
        bp: Flask blueprint
    """

    @bp.route("/health", methods=["GET"])
    def health_check() -> Response:
        """
        Health check endpoint.

        Returns:
            Health status information
        """
        return jsonify(
            {
                "status": "ok",
                "version": "1.0.0",
                "environment": current_app.config["SETTINGS"].environment,
            }
        )

    @bp.route("/webhook", methods=["POST"])
    @auth_required
    def process_prompt() -> Response:
        """
        Process a prompt with the configured LLM provider.

        Requires authentication via API token.

        Returns:
            Processed result from LLM
        """
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
        return jsonify(
            {"summary": result, "processing_time": round(processing_time, 2)}
        )
