"""
API Middleware Package

Contains middleware for FastAPI application:
- Rate limiting
- API key authentication
- Error handling
- Logging
"""

from .rate_limit import (
    RateLimitMiddleware,
    rate_limit_check,
    rate_limit_exception_handler,
    get_rate_limit_info,
    rate_limit,
    scan_rate_limiter,
    predict_rate_limiter,
    batch_rate_limiter
)

from .api_key_auth import (
    APIKey,
    APIKeyManager,
    api_key_manager,
    get_api_key_from_request,
    verify_api_key,
    require_api_key,
    require_api_key_scopes,
    get_api_key_rate_limit
)

from .error_handler import (
    ErrorResponse,
    error_handler,
    http_exception_handler,
    validation_exception_handler,
    custom_exception_handler,
    AuthenticationError,
    AuthorizationError,
    RateLimitExceededError,
    NotFoundError,
    ValidationError
)

from .logging import (
    RequestLoggingMiddleware,
    ResponseLoggingMiddleware,
    LoggingContext,
    get_logging_context
)

__all__ = [
    # Rate limiting
    'RateLimitMiddleware',
    'rate_limit_check',
    'rate_limit_exception_handler',
    'get_rate_limit_info',
    'rate_limit',
    'scan_rate_limiter',
    'predict_rate_limiter',
    'batch_rate_limiter',

    # API key authentication
    'APIKey',
    'APIKeyManager',
    'api_key_manager',
    'get_api_key_from_request',
    'verify_api_key',
    'require_api_key',
    'require_api_key_scopes',
    'get_api_key_rate_limit',

    # Error handling
    'ErrorResponse',
    'error_handler',
    'http_exception_handler',
    'validation_exception_handler',
    'custom_exception_handler',
    'AuthenticationError',
    'AuthorizationError',
    'RateLimitExceededError',
    'NotFoundError',
    'ValidationError',

    # Logging
    'RequestLoggingMiddleware',
    'ResponseLoggingMiddleware',
    'LoggingContext',
    'get_logging_context'
]
