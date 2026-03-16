"""
API Middleware - Rate Limiting

Rate limiting middleware for FastAPI application.
"""

from fastapi import Request, HTTPException, status
from slowapi import Limiter, _rate_limit_exceeded
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import time
import redis.asyncio as redis
import json

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


class RateLimitConfig:
    """Rate limit configuration."""
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        requests_per_day: int = 10000,
        burst: int = 5
        block_duration: int = 60
        enabled: bool = True
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests_per_day = requests_per_day
        self.burst = burst
        self.block_duration = block_duration
        self.enabled = enabled


# Default rate limit configuration
rate_limit_config = RateLimitConfig(
    requests_per_minute=60,    # 60 requests per minute
    requests_per_hour=1000,   # 1000 requests per hour
    requests_per_day=10000,   # 10000 requests per day
    burst=5,                # Allow burst of 5 requests
    block_duration=60,       # Block for 60 seconds after limit exceeded
    enabled=True
)

# Redis storage for rate limiting
redis_storage_url = "redis://localhost:6379"
redis_storage = redis.from_url(redis_storage_url)

# Configure rate limiter
limiter_limiter = limiter._Limiter(
    rate_limit_config.requests_per_minute,
    strategy="fixed-window"
)


class RateLimitMiddleware:
    """Rate limiting middleware for FastAPI."""

    def __init__(self, config: RateLimitConfig = None):
        """
        Initialize rate limiting middleware.

        Args:
            config: Rate limit configuration
        """
        self.config = config or rate_limit_config
        self.redis_client = None

    async def init_redis(self):
        """Initialize Redis client."""
        try:
            self.redis_client = await redis.from_url(redis_storage_url)
            await self.redis_client.ping()
            print("Rate limiting middleware initialized with Redis")
        except Exception as e:
            print(f"Warning: Could not initialize Redis: {e}")
            print("Rate limiting middleware using in-memory storage")
            self.redis_client = None

    def is_enabled(self) -> bool:
        """Check if rate limiting is enabled."""
        return self.config.enabled

    def should_rate_limit(self, request: Request, user_id: Optional[str] = None) -> bool:
        """
        Determine if request should be rate limited.

        Args:
            request: FastAPI request
            user_id: Optional user ID for per-user rate limiting

        Returns:
            True if should rate limit, False otherwise
        """
        # Check if rate limiting is enabled
        if not self.is_enabled():
            return False

        # Check for admin users (no rate limit for admins)
        user_role = getattr(request.state, 'user_role', None)
        if user_role == 'admin':
            return False

        # Check for API keys (different rate limits)
        api_key = request.headers.get('X-API-Key', None)
        if api_key:
            # Use API key based rate limits
            api_key_limits = {
                'free': 100,      # 100 requests per minute
                'pro': 1000,      # 1000 requests per minute
                'enterprise': 10000  # 10000 requests per minute
            }

            # Determine API key type (simplified)
            api_key_type = 'free'  # In production, check from database
            self.config.requests_per_minute = api_key_limits.get(api_key_type, 100)
        else:
            # User-based rate limits (if user_id provided）
            if user_id:
                self.config.requests_per_minute = 100  # 100 requests per minute per user

        return True

    async def check_rate_limit(
        self,
        request: Request,
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Check if request should be rate limited.

        Args:
            request: FastAPI request
            user_id: Optional user ID

        Returns:
            Rate limit info if limited, None otherwise
        """
        if not self.should_rate_limit(request, user_id):
            return None

        # Check if already blocked
        block_key = f"blocked:{get_remote_address(request)}"
        if self.redis_client:
            is_blocked = await self.redis_client.get(block_key)
            if is_blocked:
                ttl = await self.redis_client.ttl(block_key)
                return {
                    'blocked': True,
                    'ttl': int(ttl),
                    'message': 'Rate limit exceeded',
                    'retry_after': int(ttl)
                }

        # Check rate limits
        key = self._get_rate_limit_key(request, user_id)

        try:
            info = limiter_limiter.hit(key)

            if not info:
                return None

            # Check if rate limit exceeded
            if info.limiter:
                limit_info = {
                    'limit': self.config.requests_per_minute,
                    'remaining': info.remaining,
                    'reset': info.reset,
                    'blocked': True,
                    'message': f"Rate limit exceeded: {self.config.requests_per_minute} requests per minute"
                }

                # Block client temporarily
                if self.redis_client:
                    block_expiry = datetime.utcnow() + timedelta(seconds=self.config.block_duration)
                    block_ttl = self.config.block_duration
                    await self.redis_client.setex(
                        block_key,
                        json.dumps({'blocked_at': datetime.utcnow().isoformat()}),
                        int(block_ttl)
                    )

                return limit_info

        except RateLimitExceeded as e:
            # Rate limit exceeded
            limit_info = {
                'limit': self.config.requests_per_minute,
                'remaining': e.remaining,
                'reset': e.reset,
                'blocked': True,
                'message': f"Rate limit exceeded: {self.config.requests_per_minute} requests per minute"
            }

            # Block client temporarily
            if self.redis_client:
                block_key = f"blocked:{get_remote_address(request)}"
                block_expiry = datetime.utcnow() + timedelta(seconds=self.config.block_duration)
                block_ttl = self.config.block_duration
                await self.redis_client.setex(
                    block_key,
                    json.dumps({'blocked_at': datetime.utcnow().isoformat()}),
                    int(block_ttl)
                )

            return limit_info

        return None

    def _get_rate_limit_key(self, request: Request, user_id: Optional[str] = None) -> str:
        """
        Get rate limit key for request.

        Args:
            request: FastAPI request
            user_id: Optional user ID

        Returns:
            Rate limit key
        """
        # Use IP address as base key
        ip = get_remote_address(request)

        # Add user ID if available
        if user_id:
            return f"rate_limit:{ip}:{user_id}"

        # Add endpoint to key
        endpoint = request.url.path
        return f"rate_limit:{ip}:{endpoint}"


# Create rate limiting middleware instance
rate_limit_middleware = RateLimitMiddleware(rate_limit_config)


async def rate_limit_check(request: Request, user_id: Optional[str] = None):
    """
    Check rate limit for request.

    Args:
        request: FastAPI request
        user_id: Optional user ID

    Returns:
        Rate limit info if limited, None otherwise
    """
    # Initialize Redis on first call
    if rate_limit_middleware.redis_client is None:
        await rate_limit_middleware.init_redis()

    # Check rate limit
    return await rate_limit_middleware.check_rate_limit(request, user_id)


def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded) -> HTTPException:
    """
    Handle rate limit exceeded exception.

    Args:
        request: FastAPI request
        exc: Rate limit exceeded exception

    Returns:
        HTTPException with rate limit info
    """
    retry_after = int(exc.retry_after) if hasattr(exc, 'retry_after') else 60

    headers = {
        'X-RateLimit-Limit': str(exc.limit),
        'X-RateLimit-Remaining': str(exc.remaining),
        'X-RateLimit-Reset': str(exc.reset),
        'Retry-After': str(retry_after)
    }

    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=f"Rate limit exceeded. Retry after {retry_after} seconds",
        headers=headers
    )


def get_rate_limit_info(limit_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get rate limit info for response headers.

    Args:
        limit_info: Rate limit info

    Returns:
        Rate limit info for headers
    """
    return {
        'X-RateLimit-Limit': str(limit_info.get('limit', 0)),
        'X-RateLimit-Remaining': str(limit_info.get('remaining', 0)),
        'X-RateLimit-Reset': str(limit_info.get('reset', 0))
    }


# Rate limiter decorator
def rate_limit(requests_per_minute: int = None):
    """
    Rate limit decorator for specific endpoints.

    Args:
        requests_per_minute: Number of requests per minute

    Returns:
        Rate limiter decorator
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Check rate limit
            request = kwargs.get('request')
            if request:
                limit_info = await rate_limit_check(request)

                if limit_info and limit_info.get('blocked'):
                    headers = get_rate_limit_info(limit_info)
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded",
                        headers=headers
                    )

            # Call function
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Per-endpoint rate limiters
scan_rate_limiter = rate_limit(requests_per_minute=10)  # 10 scans per minute
predict_rate_limiter = rate_limit(requests_per_minute=30)  # 30 predictions per minute
batch_rate_limiter = rate_limit(requests_per_minute=2)  # 2 batch requests per minute
