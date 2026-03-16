"""
API Middleware - Logging

Structured logging middleware for FastAPI application.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Dict, Any
import logging
import time
import json
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request logging middleware."""

    async def dispatch(self, request: Request, call_next: Callable):
        """Dispatch request with logging."""
        start_time = time.time()

        # Generate request ID
        request_id = str(uuid.uuid4())

        # Store request ID in state
        request.state.request_id = request_id
        request.state.start_time = start_time

        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url}",
            extra={
                'request_id': request_id,
                'url': str(request.url),
                'method': request.method,
                'path': request.url.path,
                'query_params': str(request.query_params),
                'client': request.client.host if request.client else None,
                'user_agent': request.headers.get('user-agent'),
                'content_type': request.headers.get('content-type'),
                'content_length': request.headers.get('content-length'),
                'timestamp': datetime.utcnow().isoformat()
            }
        )

        # Call next middleware
        response = await call_next(request)

        # Calculate response time
        process_time = time.time() - start_time

        # Log response
        logger.info(
            f"[{request_id}] {request.method} {request.url} - {response.status_code}",
            extra={
                'request_id': request_id,
                'status_code': response.status_code,
                'process_time_ms': process_time * 1000,
                'response_size': response.headers.get('content-length'),
                'timestamp': datetime.utcnow().isoformat()
            }
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response


class ResponseLoggingMiddleware(BaseHTTPMiddleware):
    """Response logging middleware."""

    async def dispatch(self, request: Request, call_next: Callable):
        """Dispatch response with logging."""
        response = await call_next(request)

        # Get request ID
        request_id = getattr(request.state, 'request_id', None)

        if request_id:
            # Log response body (if JSON)
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    body = await response.body()

                    if body:
                        # Try to parse JSON
                        try:
                            json_body = json.loads(body)
                            logger.info(
                                f"[{request_id}] Response body",
                                extra={
                                    'request_id': request_id,
                                    'response_body': json_body
                                }
                            )
                        except:
                            # Not valid JSON
                            pass
                except:
                    pass

        return response


# Logging context manager
class LoggingContext:
    """Logging context manager for structured logging."""

    def __init__(self, request: Request):
        """
        Initialize logging context.

        Args:
            request: FastAPI request
        """
        self.request_id = getattr(request.state, 'request_id', 'none')
        self.user_id = getattr(request.state, 'user_id', None)
        self.client = getattr(request.state, 'client', None)
        self.method = request.method
        self.path = request.url.path

    def info(self, message: str, extra: Dict[str, Any] = None):
        """
        Log info message.

        Args:
            message: Log message
            extra: Extra context data
        """
        log_extra = {
            'request_id': self.request_id,
            'user_id': self.user_id,
            'client': str(self.client) if self.client else 'none',
            'method': self.method,
            'path': self.path
        }

        if extra:
            log_extra.update(extra)

        logger.info(f"[{self.request_id}] {message}", extra=log_extra)

    def warning(self, message: str, extra: Dict[str, Any] = None):
        """
        Log warning message.

        Args:
            message: Log message
            extra: Extra context data
        """
        log_extra = {
            'request_id': self.request_id,
            'user_id': self.user_id,
            'client': str(self.client) if self.client else 'none',
            'method': self.method,
            'path': self.path
        }

        if extra:
            log_extra.update(extra)

        logger.warning(f"[{self.request_id}] {message}", extra=log_extra)

    def error(self, message: str, extra: Dict[str, Any] = None):
        """
        Log error message.

        Args:
            message: Log message
            extra: Extra context data
        """
        log_extra = {
            'request_id': self.request_id,
            'user_id': self.user_id,
            'client': str(self.client) if self.client else 'none',
            'method': self.method,
            'path': self.path
        }

        if extra:
            log_extra.update(extra)

        logger.error(f"[{self.request_id}] {message}", extra=log_extra)

    def debug(self, message: str, extra: Dict[str, Any] = None):
        """
        Log debug message.

        Args:
            message: Log message
            extra: Extra context data
        """
        log_extra = {
            'request_id': self.request_id,
            'user_id': self.user_id,
            'client': str(self.client) if self.client else 'none',
            'method': self.method,
            'path': self.path
        }

        if extra:
            log_extra.update(extra)

        logger.debug(f"[{self.request_id}] {message}", extra=log_extra)


def get_logging_context(request: Request) -> LoggingContext:
    """
    Get logging context for request.

    Args:
        request: FastAPI request

    Returns:
        Logging context
    """
    return LoggingContext(request)
