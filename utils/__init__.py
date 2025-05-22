# flaskllm/utils/__init__.py
"""
Utilities Package

This package provides various utility functions for the FlaskLLM application.
"""

# Import and expose file processor utilities
from .file_processor import (
    read_text_file,
    write_text_file,
    read_json_file,
    write_json_file,
    read_csv_file,
    write_csv_file,
    ensure_directory,
    list_files,
    copy_file,
    move_file,
    delete_file,
)

# Import and expose logging utilities
from .logger import (
    get_structured_logger,
    configure_app_logging,
    DEBUG,
    INFO,
    WARNING,
    ERROR,
    CRITICAL,
)

# Import and expose configuration loading utilities
from .config_loader import (
    load_json_config,
    load_env_config,
    merge_configs,
    get_config_value,
)

# Import and expose validation utilities
from .validation import (
    validate_string,
    validate_email,
    validate_url,
    validate_integer,
    validate_float,
    validate_boolean,
    validate_date,
    validate_ip_address,
    validate_dict,
    validate_list,
)

# Import and expose rate limiting utilities
from .rate_limiter import (
    configure_rate_limiting,
    apply_rate_limit,
    get_rate_limit_key,
)

# Import and expose security utilities
from .security import (
    generate_secure_token,
    sanitize_string,
    sanitize_input,
    mask_sensitive_data,
)

# Import and expose Prometheus metrics utilities
from .prometheus_metrics import (
    init_metrics,
    track_llm_request,
    track_llm_tokens,
    track_cache_operation,
    instrument_llm_handler,
)

__all__ = [
    # File processor utilities
    'read_text_file',
    'write_text_file',
    'read_json_file',
    'write_json_file',
    'read_csv_file',
    'write_csv_file',
    'ensure_directory',
    'list_files',
    'copy_file',
    'move_file',
    'delete_file',
    
    # Logging utilities
    'get_structured_logger',
    'configure_app_logging',
    'DEBUG',
    'INFO',
    'WARNING',
    'ERROR',
    'CRITICAL',
    
    # Configuration loading utilities
    'load_json_config',
    'load_env_config',
    'merge_configs',
    'get_config_value',
    
    # Validation utilities
    'validate_string',
    'validate_email',
    'validate_url',
    'validate_integer',
    'validate_float',
    'validate_boolean',
    'validate_date',
    'validate_ip_address',
    'validate_dict',
    'validate_list',
    
    # Rate limiting utilities
    'configure_rate_limiting',
    'apply_rate_limit',
    'get_rate_limit_key',
    
    # Security utilities
    'generate_secure_token',
    'sanitize_string',
    'sanitize_input',
    'mask_sensitive_data',
    
    # Prometheus metrics utilities
    'init_metrics',
    'track_llm_request',
    'track_llm_tokens',
    'track_cache_operation',
    'instrument_llm_handler',
]