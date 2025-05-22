# flaskllm/api/v1/health_check.py
"""
Health Check API Routes

This module provides detailed health check endpoints for the API,
including system information, dependency statuses, and configuration details.
"""

import sys
import platform
import time
from typing import Dict, Any, Tuple

from flask import current_app
from flask_restx import Api, Resource, Namespace, fields

from core.logging import get_logger
from core.exceptions import APIError

logger = get_logger(__name__)


def register_health_routes(api: Api, parent_ns: Namespace = None) -> None:
    """
    Register health check routes with the API.
    
    Args:
        api: Flask-RESTX API instance
        parent_ns: Parent namespace to register routes under (optional)
    """
    # Use parent namespace if provided, otherwise create a new one
    ns = parent_ns or api.namespace('/health', description='Health Check Operations')
    
    # Define response models
    system_info_model = api.model('SystemInfo', {
        'python_version': fields.String(description='Python version'),
        'platform': fields.String(description='Operating system platform'),
        'dependencies': fields.Raw(description='Dependency versions'),
        'memory_usage': fields.Raw(description='Memory usage statistics'),
    })
    
    database_status_model = api.model('DatabaseStatus', {
        'status': fields.String(description='Database connection status'),
        'latency_ms': fields.Float(description='Database latency in milliseconds'),
        'type': fields.String(description='Database type'),
    })
    
    cache_status_model = api.model('CacheStatus', {
        'status': fields.String(description='Cache connection status'),
        'type': fields.String(description='Cache backend type'),
        'hit_rate': fields.Float(description='Cache hit rate percentage'),
    })
    
    llm_status_model = api.model('LLMStatus', {
        'provider': fields.String(description='LLM provider name'),
        'status': fields.String(description='LLM provider status'),
        'models_available': fields.List(fields.String, description='Available models'),
    })
    
    detailed_health_model = api.model('DetailedHealth', {
        'status': fields.String(description='Overall API status'),
        'version': fields.String(description='API version'),
        'uptime_seconds': fields.Integer(description='API uptime in seconds'),
        'system': fields.Nested(system_info_model),
        'database': fields.Nested(database_status_model),
        'cache': fields.Nested(cache_status_model),
        'llm': fields.Nested(llm_status_model),
    })
    
    # Register routes only if parent namespace is not provided
    # Otherwise, they will be registered by the parent module
    if not parent_ns:
        # Simple health check endpoint (already in routes.py)
        @ns.route('/')
        class HealthCheck(Resource):
            @ns.doc(description='Basic health check endpoint')
            @ns.response(200, 'Success')
            def get(self) -> Tuple[Dict[str, Any], int]:
                """Basic health check endpoint."""
                settings = current_app.config.get("SETTINGS")
                if not settings:
                    return {"status": "error", "error": "Configuration missing"}, 500
                    
                return {"status": "ok", "version": api.version}, 200
    
    # Detailed health check endpoint
    @ns.route('/detail')
    class DetailedHealthCheck(Resource):
        @ns.doc(description='Detailed health check with system information')
        @ns.response(200, 'Success', detailed_health_model)
        def get(self) -> Tuple[Dict[str, Any], int]:
            """Detailed health check with system information."""
            try:
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
                    "version": getattr(api, 'version', '1.0.0'),
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
                
                return response, 200
            except Exception as e:
                logger.error("Error in detailed health check", error=str(e))
                return {"status": "error", "error": str(e)}, 500


def _get_dependency_versions() -> Dict[str, str]:
    """
    Get versions of key dependencies.
    
    Returns:
        Dictionary of dependency names and versions
    """
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


def _get_memory_usage() -> Dict[str, Any]:
    """
    Get memory usage statistics.
    
    Returns:
        Dictionary of memory usage metrics
    """
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


def _check_database_status(settings) -> Dict[str, Any]:
    """
    Check database connection status.
    
    Args:
        settings: Application settings
        
    Returns:
        Dictionary with database status information
    """
    # This is a simplified implementation - in a real app,
    # you would actually test the database connection
    try:
        return {
            "status": "connected",
            "latency_ms": 0.5,  # Placeholder
            "type": "sqlite",  # Placeholder
        }
    except Exception as e:
        logger.warning("Database status check failed", error=str(e))
        return {"status": "error", "error": str(e)}


def _check_cache_status(settings) -> Dict[str, Any]:
    """
    Check cache backend status.
    
    Args:
        settings: Application settings
        
    Returns:
        Dictionary with cache status information
    """
    try:
        # Get cache backend type from settings
        cache_type = getattr(settings, "cache_backend", "memory")
        
        return {
            "status": "connected",
            "type": cache_type,
            "hit_rate": 95.5,  # Placeholder
        }
    except Exception as e:
        logger.warning("Cache status check failed", error=str(e))
        return {"status": "error", "error": str(e)}


def _check_llm_status(settings) -> Dict[str, Any]:
    """
    Check LLM provider status.
    
    Args:
        settings: Application settings
        
    Returns:
        Dictionary with LLM provider status information
    """
    try:
        # Get LLM provider from settings
        provider = getattr(settings, "llm_provider", "unknown")
        
        # This would be replaced with actual checks in a real implementation
        return {
            "provider": provider,
            "status": "connected",
            "models_available": ["gpt-3.5-turbo", "gpt-4"], # Placeholder
        }
    except Exception as e:
        logger.warning("LLM status check failed", error=str(e))
        return {"status": "error", "provider": getattr(settings, "llm_provider", "unknown"), "error": str(e)}
