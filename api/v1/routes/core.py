# api/v1/routes/core.py - Fixed route registration
"""
Core API Routes

This module contains the core API routes for the application, including:
- Health check endpoints
- Main LLM processing endpoints
- Basic application routes
"""
import time
from flask import Blueprint, Response, current_app, jsonify, request
from api.v1.schemas.common import PromptRequest, PromptResponse, validate_request
from core.auth import auth_required
from core.exceptions import InvalidInputError
from core.logging import get_logger

# Import get_llm_handler lazily to avoid circular imports
# We'll import it only when needed in the route functions

# Create a blueprint for the core routes
bp = Blueprint('core', __name__)
logger = get_logger(__name__)

# Health check routes
@bp.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint."""
    settings = current_app.config.get("SETTINGS")
    if not settings:
        return {"status": "error", "error": "Configuration missing"}, 500
        
    return {"status": "ok", "version": "1.0"}, 200

@bp.route('/health/detail', methods=['GET'])
def detailed_health_check():
    """Detailed health check with system information."""
    try:
        import sys
        import platform
        import time
        
        # Get settings from app config
        settings = current_app.config.get("SETTINGS")
        if not settings:
            logger.error("Settings not found in app config")
            return {"status": "error", "error": "Configuration missing"}, 500
        
        # Get start time from app config or use current time
        start_time = getattr(current_app, 'start_time', time.time())
        uptime = int(time.time() - start_time)
        
        # Build response
        response = {
            "status": "ok",
            "version": "1.0",
            "uptime_seconds": uptime,
            "system": {
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "platform": platform.platform(),
                "dependencies": _get_dependency_versions(),
                "memory_usage": _get_memory_usage(),
            },
            "database": _check_database_status(settings),
            "cache": _check_cache_status(settings),
            "llm": _check_llm_status(settings),
        }
        
        return jsonify(response), 200
    except Exception as e:
        logger.error("Error in detailed health check", error=str(e))
        return {"status": "error", "error": str(e)}, 500

# Main webhook route for processing prompts
@bp.route('/webhook', methods=['POST'])
@auth_required
def process_prompt():
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
        
        # Get LLM handler
        # Import lazily to avoid circular imports
        from llm.factory import get_llm_handler
        llm_handler = get_llm_handler(current_app.config.get("SETTINGS"))
        
        # Process the prompt
        start_time = time.time()
        result = llm_handler.process_prompt(
            prompt=prompt_request.prompt,
            source=prompt_request.source.value if prompt_request.source else None,
            language=prompt_request.language,
            type=prompt_request.type.value if prompt_request.type else None,
            **prompt_request.additional_params
        )
        processing_time = time.time() - start_time
        
        # Create response
        response_data = {
            "result": result,
            "processing_time": processing_time
        }
        
        return jsonify(response_data), 200
        
    except InvalidInputError as e:
        logger.warning("Invalid request data", error=str(e))
        return {"error": str(e)}, 400
    except Exception as e:
        logger.error("Unexpected error during request processing", error=str(e))
        return {"error": f"Failed to process request: {str(e)}"}, 500

# Helper functions from health_check.py
def _get_dependency_versions():
    """Get versions of key dependencies."""
    try:
        import flask, pydantic, structlog
        
        return {
            "flask": flask.__version__,
            "pydantic": pydantic.__version__,
            "structlog": structlog.__version__,
        }
    except Exception as e:
        logger.warning("Could not get dependency versions", error=str(e))
        return {"error": "Could not retrieve dependency versions"}

def _get_memory_usage():
    """Get memory usage statistics."""
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss_mb": memory_info.rss / (1024 * 1024),
            "vms_mb": memory_info.vms / (1024 * 1024),
            "percent": process.memory_percent(),
        }
    except ImportError:
        return {"note": "psutil not installed, memory usage unavailable"}
    except Exception as e:
        logger.warning("Could not get memory usage", error=str(e))
        return {"error": "Could not retrieve memory usage"}

def _check_database_status(settings):
    """Check database connection status."""
    try:
        return {
            "status": "connected",
            "latency_ms": 0.5,  # Placeholder
            "type": "sqlite",  # Placeholder
        }
    except Exception as e:
        logger.warning("Database status check failed", error=str(e))
        return {"status": "error", "error": str(e)}

def _check_cache_status(settings):
    """Check cache backend status."""
    try:
        return {
            "status": "connected",
            "type": "in-memory",  # Placeholder
            "hit_rate": 0.75,  # Placeholder
        }
    except Exception as e:
        logger.warning("Cache status check failed", error=str(e))
        return {"status": "error", "error": str(e)}

def _check_llm_status(settings):
    """Check LLM provider status."""
    try:
        # Lightweight check - just verify we can create the handler
        from llm.factory import get_llm_handler
        llm_handler = get_llm_handler(settings)
        
        return {
            "provider": settings.llm_provider,
            "status": "connected",
            "models_available": [settings.openai_model],
        }
    except Exception as e:
        logger.warning("LLM status check failed", error=str(e))
        return {
            "provider": getattr(settings, "llm_provider", "unknown"),
            "status": "error",
            "error": str(e),
        }