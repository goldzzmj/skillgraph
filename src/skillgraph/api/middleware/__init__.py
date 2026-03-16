"""
API Middleware Package

Contains middleware for FastAPI application:
- Rate limiting
- API key authentication
- Permission control
- OAuth 2.0 scopes
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

from .permission import (
    Permission,
    Role,
    Scope,
    has_permission,
    has_scope_permission,
    require_permission,
    require_permissions,
    require_role,
    require_any_role,
    require_scope,
    require_any_scope,
    require_scope_permission,
    require_api_key_permissions,
    get_current_user,
    check_api_key_permissions,
    inherits_permission
)

from .oauth_scopes import (
    OAUTH_SCOPES,
    ScopePermission,
    get_scope_permissions,
    validate_scopes,
    check_scope_permissions,
    get_all_scopes,
    get_scope_for_permission,
    get_permissions_for_scope,
    get_scopes_for_role,
    require_oauth_scopes,
    require_any_oauth_scope
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
    'get_logging_context',

    # Permission control
    'Permission',
    'Role',
    'Scope',
    'has_permission',
    'has_scope_permission',
    'require_permission',
    'require_permissions',
    'require_role',
    'require_any_role',
    'require_scope',
    'require_any_scope',
    'require_scope_permission',
    'require_api_key_permissions',
    'get_current_user',
    'check_api_key_permissions',
    'inherits_permission',

    # OAuth 2.0 scopes
    'OAUTH_SCOPES',
    'ScopePermission',
    'get_scope_permissions',
    'validate_scopes',
    'check_scope_permissions',
    'get_all_scopes',
    'get_scope_for_permission',
    'get_permissions_for_scope',
    'get_scopes_for_role',
    'require_oauth_scopes',
    'require_any_oauth_scope'
]
