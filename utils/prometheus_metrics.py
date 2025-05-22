# flaskllm/utils/prometheus_metrics.py
"""
Prometheus Metrics Module

This module provides utilities for instrumenting the application with Prometheus metrics
for monitoring API calls, LLM usage, and system performance.
"""

from typing import Dict, List, Optional, Union, Any
import time
from contextlib import contextmanager
from functools import wraps
from flask import Flask, request, g

try:
    from prometheus_client import Counter, Histogram, Gauge, Summary, Info
    from prometheus_client import generate_latest, REGISTRY, CONTENT_TYPE_LATEST
except ImportError:
    # Provide fallbacks for when prometheus_client is not installed
    class MetricBase:
        def __init__(self, *args, **kwargs):
            pass
        
        def inc(self, *args, **kwargs):
            pass
        
        def observe(self, *args, **kwargs):
            pass
        
        def set(self, *args, **kwargs):
            pass
        
        def labels(self, *args, **kwargs):
            return self
    
    # Define mock classes
    Counter = Histogram = Gauge = Summary = Info = MetricBase
    
    def generate_latest(*args, **kwargs):
        return b"Prometheus client not installed"
    
    REGISTRY = None
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"

from core.logging import get_logger

# Configure logger
logger = get_logger(__name__)

# Define metrics
REQUEST_COUNT = Counter(
    'flaskllm_http_requests_total', 
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'flaskllm_http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, float('inf'))
)

LLM_REQUEST_COUNT = Counter(
    'flaskllm_llm_requests_total',
    'Total number of LLM API requests',
    ['provider', 'model', 'success']
)

LLM_REQUEST_LATENCY = Histogram(
    'flaskllm_llm_request_duration_seconds',
    'LLM API request latency in seconds',
    ['provider', 'model'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 7.5, 10.0, 15.0, 30.0, 60.0, float('inf'))
)

LLM_TOKEN_COUNT = Counter(
    'flaskllm_llm_token_count_total',
    'Total number of tokens processed by LLM',
    ['provider', 'model', 'direction']
)

ACTIVE_REQUESTS = Gauge(
    'flaskllm_active_requests',
    'Number of active HTTP requests',
    ['method']
)

CACHE_OPERATIONS = Counter(
    'flaskllm_cache_operations_total',
    'Total number of cache operations',
    ['operation', 'result']
)

SYSTEM_INFO = Info(
    'flaskllm_system',
    'System information'
)


def init_metrics(app: Flask) -> None:
    """
    Initialize Prometheus metrics for a Flask application.
    
    Args:
        app: Flask application instance
    """
    logger.info("Initializing Prometheus metrics")
    
    # Set up system info
    SYS_INFO = {
        'app_name': 'FlaskLLM',
        'version': app.config.get('VERSION', 'unknown'),
        'environment': app.config.get('ENV', 'production'),
    }
    SYSTEM_INFO.info(SYS_INFO)
    
    # Add metrics endpoint
    @app.route('/metrics', methods=['GET'])
    def metrics():
        return generate_latest(REGISTRY), 200, {'Content-Type': CONTENT_TYPE_LATEST}
    
    # Register before_request and after_request handlers
    @app.before_request
    def before_request():
        g.start_time = time.time()
        ACTIVE_REQUESTS.labels(request.method).inc()
    
    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            request_latency = time.time() - g.start_time
            endpoint = request.endpoint or 'unknown'
            REQUEST_LATENCY.labels(request.method, endpoint).observe(request_latency)
            REQUEST_COUNT.labels(request.method, endpoint, response.status_code).inc()
            ACTIVE_REQUESTS.labels(request.method).dec()
        return response
    
    logger.info("Prometheus metrics initialized successfully")


@contextmanager
def track_llm_request(provider: str, model: str):
    """
    Context manager for tracking LLM API requests.
    
    Args:
        provider: LLM provider name
        model: LLM model name
    """
    start_time = time.time()
    success = False
    
    try:
        yield
        success = True
    finally:
        request_time = time.time() - start_time
        LLM_REQUEST_LATENCY.labels(provider, model).observe(request_time)
        LLM_REQUEST_COUNT.labels(provider, model, 'success' if success else 'failure').inc()


def track_llm_tokens(provider: str, model: str, input_tokens: int, output_tokens: int):
    """
    Track LLM token usage.
    
    Args:
        provider: LLM provider name
        model: LLM model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
    """
    LLM_TOKEN_COUNT.labels(provider, model, 'input').inc(input_tokens)
    LLM_TOKEN_COUNT.labels(provider, model, 'output').inc(output_tokens)


def track_cache_operation(operation: str, hit: bool):
    """
    Track cache operations.
    
    Args:
        operation: Operation type (get, set, delete)
        hit: Whether the operation was a hit (for get operations)
    """
    CACHE_OPERATIONS.labels(operation, 'hit' if hit else 'miss').inc()


def instrument_llm_handler(func):
    """
    Decorator for instrumenting LLM handler methods with Prometheus metrics.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        provider = getattr(self, 'provider_name', type(self).__name__)
        model = getattr(self, 'model', 'unknown')
        
        with track_llm_request(provider, model):
            result = func(self, *args, **kwargs)
            
            # If token counts are available (returned or stored as instance variables),
            # track them as well
            input_tokens = getattr(self, 'last_input_tokens', 0)
            output_tokens = getattr(self, 'last_output_tokens', 0)
            if input_tokens or output_tokens:
                track_llm_tokens(provider, model, input_tokens, output_tokens)
                
            return result
    
    return wrapper


@pytest.mark.skipif(not os.environ.get("OPENROUTER_API_KEY"), reason="OpenRouter API key not available")
def test_openrouter_provider():
    """Test OpenRouter provider with a real API call."""
    # Create app with OpenRouter provider
    app = create_app(Settings(
        environment="testing",
        api_token="test_token",
        llm_provider=LLMProvider.OPENROUTER,
        openrouter_api_key=os.environ.get("OPENROUTER_API_KEY"),
        openrouter_model="openai/gpt-4o",
        request_timeout=30
    ))

    with app.app_context():
        # Get the handler
        handler = get_llm_handler(current_app.config["SETTINGS"])

        # Call the API
        result = handler.process_prompt(
            prompt="What is the capital of Germany?",
            type="summary"
        )

        # Verify result contains Berlin
        assert "Berlin" in result
