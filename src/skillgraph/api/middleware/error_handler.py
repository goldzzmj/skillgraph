"""
API Middleware - Error Handling

Error handling middleware for FastAPI application.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Dict, Any, Optional, Union
from datetime import datetime
import traceback
import uuid
import logging

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Standardized error response."""
    def __init__(
        self,
        error: str,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error = error
        self.message = message
        self.status_code = status_code
        self.request_id = request_id or str(uuid.uuid4())
        self.timestamp = datetime.utcnow().isoformat()
        self.details = details

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'error': self.error,
            'message': self.message,
            'status_code': self.status_code,
            'request_id': self.request_id,
            'timestamp': self.timestamp,
            'details': self.details
        }


async def log_error_to_sentry(request: Request, exc: Exception):
    """
    Log error to Sentry (for production).

    Args:
        request: FastAPI request
        exc: Exception
    """
    # In production, send to Sentry
    # For now, just log
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        exc_info=True,
        extra={
            'request_id': getattr(request.state, 'request_id', None),
            'url': str(request.url),
            'method': request.method,
            'client': getattr(request.state, 'client', None)
        }
    )


async def log_request(request: Request):
    """
    Log request information.

    Args:
        request: FastAPI request
    """
    request_id = str(uuid.uuid4())

    # Store request_id in state
    request.state.request_id = request_id

    # Log request
    logger.info(
        f"Request: {request.method} {request.url}",
        extra={
            'request_id': request_id,
            'url': str(request.url),
            'method': request.method,
            'client': getattr(request.state, 'client', None),
            'user_id': getattr(request.state, 'user_id', None),
            'path': request.url.path,
            'query_params': str(request.query_params)
        }
    )

    return request_id


async def log_response(request: Request, status_code: int, response_time: float):
    """
    Log response information.

    Args:
        request: FastAPI request
        status_code: Response status code
        response_time: Response time in seconds
    """
    request_id = getattr(request.state, 'request_id', None)

    logger.info(
        f"Response: {request.method} {request.url} - {status_code}",
        extra={
            'request_id': request_id,
            'status_code': status_code,
            'response_time_ms': response_time * 1000,
            'path': request.url.path
        }
    )


async def error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler.

    Args:
        request: FastAPI request
        exc: Exception

    Returns:
        JSON response with error info
    """
    # Log error
    await log_error_to_sentry(request, exc)

    # Get request_id
    request_id = getattr(request.state, 'request_id', None)

    # Handle different exception types
    if isinstance(exc, StarletteHTTPException):
        # Starlette/FastAPI HTTP exceptions
        status_code = exc.status_code
        message = str(exc.detail)

    elif isinstance(exc, RequestValidationError):
        # Pydantic validation errors
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        message = "Validation error"

        # Extract validation errors
        details = {
            'validation_errors': exc.errors()
        }

    elif isinstance(exc, ValueError):
        # Value errors
        status_code = status.HTTP_400_BAD_REQUEST
        message = str(exc)
        details = {'value_error': str(exc)}

    elif isinstance(exc, PermissionError):
        # Permission errors
        status_code = status.HTTP_403_FORBIDDEN
        message = "Permission denied"
        details = {'permission_denied': True}

    elif isinstance(exc, FileNotFoundError):
        # File not found errors
        status_code = status.HTTP_404_NOT_FOUND
        message = "Resource not found"
        details = {'resource_not_found': True}

    else:
        # Other exceptions
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        message = "Internal server error"

        # Don't expose details for 500 errors
        if status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
            details = None
        else:
            details = {
                'exception': type(exc).__name__,
                'exception_message': str(exc)
            }

    # Create error response
    error_response = ErrorResponse(
        error=type(exc).__name__,
        message=message,
        status_code=status_code,
        request_id=request_id,
        details=details
    )

    # Log error
    logger.error(
        f"Error: {error_response.error} - {error_response.message}",
        exc_info=True,
        extra={
            'request_id': request_id,
            'status_code': status_code,
            'error': error_response.error
        }
    )

    # Return JSON response
    return JSONResponse(
        status_code=status_code,
        content=error_response.to_dict()
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    """
    HTTP exception handler.

    Args:
        request: FastAPI request
        exc: HTTPException

    Returns:
        JSON response with HTTP error info
    """
    # Get request_id
    request_id = getattr(request.state, 'request_id', None)

    # Create error response
    error_response = ErrorResponse(
        error=type(exc).__name__,
        message=str(exc.detail),
        status_code=exc.status_code,
        request_id=request_id,
        details={'http_exception': True}
    )

    # Log error
    logger.warning(
        f"HTTP Error: {error_response.error} - {error_response.message}",
        extra={
            'request_id': request_id,
            'status_code': exc.status_code,
            'error': error_response.error
        }
    )

    # Return JSON response with custom headers
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.to_dict()
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Validation exception handler.

    Args:
        request: FastAPI request
        exc: RequestValidationError

    Returns:
        JSON response with validation errors
    """
    # Get request_id
    request_id = getattr(request.state, 'request_id', None)

    # Extract validation errors
    validation_errors = exc.errors()

    # Format errors
    formatted_errors = []
    for error in validation_errors:
        formatted_errors.append({
            'field': '.'.join(error['loc']),
            'message': error['msg'],
            'type': error['type']
        })

    # Create error response
    error_response = ErrorResponse(
        error="ValidationError",
        message="Request validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        request_id=request_id,
        details={'validation_errors': formatted_errors}
    )

    # Log validation error
    logger.warning(
        f"Validation Error: {len(formatted_errors)} errors",
        extra={
            'request_id': request_id,
            'errors': formatted_errors
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.to_dict()
    )


def custom_exception_handler(
    error_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    error_name: str = "InternalError"
):
    """
    Decorator for custom exception handlers.

    Args:
        error_code: HTTP status code
        error_name: Error name

    Returns:
        Exception handler decorator
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Get request from kwargs
                request = kwargs.get('request')

                if not request:
                    raise

                # Create error response
                error_response = ErrorResponse(
                    error=error_name,
                    message=str(e),
                    status_code=error_code,
                    request_id=getattr(request.state, 'request_id', None),
                    details={
                        'custom_exception': True,
                        'exception_message': str(e),
                        'traceback': traceback.format_exc()
                    }
                )

                logger.error(
                    f"{error_name}: {str(e)}",
                    exc_info=True,
                    extra={
                        'request_id': error_response.request_id,
                        'error': error_name
                    }
                )

                return JSONResponse(
                    status_code=error_code,
                    content=error_response.to_dict()
                )

        return wrapper

    return decorator


# Custom exception classes
class AuthenticationError(Exception):
    """Authentication exception."""
    def __init__(self, message: str = "Authentication failed"):
        self.message = message
        super().__init__(self.message)


class AuthorizationError(Exception):
    """Authorization exception."""
    def __init__(self, message: str = "Authorization failed"):
        self.message = message
        super().__init__(self.message)


class RateLimitExceededError(Exception):
    """Rate limit exceeded exception."""
    def __init__(self, message: str = "Rate limit exceeded"):
        self.message = message
        super().__init__(self.message)


class NotFoundError(Exception):
    """Not found exception."""
    def __init__(self, message: str = "Resource not found"):
        self.message = message
        super().__init__(self.message)


class ValidationError(Exception):
    """Validation exception."""
    def __init__(self, message: str = "Validation failed"):
        self.message = message
        super().__init__(self.message)
