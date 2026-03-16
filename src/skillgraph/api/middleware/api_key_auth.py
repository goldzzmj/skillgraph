"""
API Middleware - API Key Authentication

API key authentication middleware for FastAPI application.
"""

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import secrets
import hashlib
from datetime import datetime, timedelta
import json

# API key model
class APIKey:
    """API key model."""
    def __init__(
        self,
        key_id: str,
        key_value: str,
        name: str,
        scopes: list,
        rate_limit: int,
        is_active: bool,
        created_at: datetime,
        expires_at: Optional[datetime] = None,
        owner_id: Optional[str] = None
    ):
        self.key_id = key_id
        self.key_value = key_value
        self.name = name
        self.scopes = scopes
        self.rate_limit = rate_limit
        self.is_active = is_active
        self.created_at = created_at
        self.expires_at = expires_at
        self.owner_id = owner_id

    def is_valid(self) -> bool:
        """Check if API key is valid."""
        if not self.is_active:
            return False

        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'key_id': self.key_id,
            'name': self.name,
            'scopes': self.scopes,
            'rate_limit': self.rate_limit,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }


# Mock API key storage (in production, use database)
API_KEYS_DB: Dict[str, APIKey] = {}


class APIKeyManager:
    """API key manager for generating and validating API keys."""

    def __init__(self):
        """Initialize API key manager."""
        # Initialize with some default keys
        self._initialize_default_keys()

    def _initialize_default_keys(self):
        """Initialize with default API keys."""
        # Default test keys
        default_keys = [
            {
                'key_value': 'sk_test_1234567890abcdef',
                'name': 'Test API Key',
                'scopes': ['scan', 'predict', 'batch'],
                'rate_limit': 1000,
                'expires_days': None
            },
            {
                'key_value': 'sk_test_0987654321fedcba',
                'name': 'Production Test Key',
                'scopes': ['scan', 'predict'],
                'rate_limit': 100,
                'expires_days': 365
            }
        ]

        for key_data in default_keys:
            api_key = APIKey(
                key_id=secrets.token_hex(16),
                key_value=key_data['key_value'],
                name=key_data['name'],
                scopes=key_data['scopes'],
                rate_limit=key_data['rate_limit'],
                is_active=True,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=key_data.get('expires_days', 365)) if key_data.get('expires_days') else None,
                owner_id=None
            )

            API_KEYS_DB[api_key.key_value] = api_key

    def generate_api_key(
        self,
        name: str,
        scopes: list = ['scan'],
        rate_limit: int = 1000,
        expires_days: Optional[int] = None,
        owner_id: Optional[str] = None
    ) -> APIKey:
        """
        Generate new API key.

        Args:
            name: API key name
            scopes: List of scopes (scan, predict, batch, admin)
            rate_limit: Requests per minute
            expires_days: Days until expiration (None for no expiration)
            owner_id: Owner user ID

        Returns:
            Generated API key
        """
        # Generate API key (prefix + random string)
        prefix = "sk_"
        random_part = secrets.token_urlsafe(32)
        key_value = f"{prefix}{random_part}"

        # Create API key object
        api_key = APIKey(
            key_id=secrets.token_hex(16),
            key_value=key_value,
            name=name,
            scopes=scopes,
            rate_limit=rate_limit,
            is_active=True,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=expires_days) if expires_days else None,
            owner_id=owner_id
        )

        # Store API key
        API_KEYS_DB[key_value] = api_key

        print(f"Generated API key: {key_value}")
        print(f"  Name: {name}")
        print(f"  Scopes: {scopes}")
        print(f"  Rate limit: {rate_limit} requests/minute")
        print(f"  Expires: {api_key.expires_at}")

        return api_key

    def validate_api_key(self, api_key_value: str, required_scopes: Optional[list] = None) -> Optional[APIKey]:
        """
        Validate API key.

        Args:
            api_key_value: API key value
            required_scopes: Required scopes (optional)

        Returns:
            API key object if valid, None otherwise
        """
        api_key = API_KEYS_DB.get(api_key_value)

        if not api_key:
            return None

        if not api_key.is_valid():
            return None

        # Check required scopes
        if required_scopes:
            for scope in required_scopes:
                if scope not in api_key.scopes:
                    return None

        return api_key

    def revoke_api_key(self, api_key_value: str) -> bool:
        """
        Revoke API key.

        Args:
            api_key_value: API key value

        Returns:
            True if revoked, False otherwise
        """
        api_key = API_KEYS_DB.get(api_key_value)

        if not api_key:
            return False

        api_key.is_active = False

        print(f"Revoked API key: {api_key_value}")

        return True

    def get_api_keys_by_owner(self, owner_id: str) -> list:
        """
        Get all API keys for owner.

        Args:
            owner_id: Owner user ID

        Returns:
            List of API keys owned by user
        """
        owner_keys = []

        for key_value, api_key in API_KEYS_DB.items():
            if api_key.owner_id == owner_id:
                owner_keys.append(api_key)

        return owner_keys

    def get_api_key_info(self, api_key_value: str) -> Optional[Dict[str, Any]]:
        """
        Get API key info.

        Args:
            api_key_value: API key value

        Returns:
            API key info
        """
        api_key = API_KEYS_DB.get(api_key_value)

        if not api_key:
            return None

        return api_key.to_dict()


# Create API key manager instance
api_key_manager = APIKeyManager()


# API key security scheme
api_key_scheme = HTTPBearer(auto_error=False)


def get_api_key_from_request(request: Request) -> Optional[str]:
    """
    Extract API key from request.

    Args:
        request: FastAPI request

    Returns:
        API key value
    """
    # Check X-API-Key header (preferred)
    api_key = request.headers.get('X-API-Key', None)

    if not api_key:
        # Check Authorization header
        try:
            auth = api_key_scheme(request)
            if auth and auth.credentials:
                api_key = auth.credentials
        except Exception:
            pass

    return api_key


async def verify_api_key(
    request: Request,
    required_scopes: Optional[list] = None
) -> Optional[APIKey]:
    """
    Verify API key from request.

    Args:
        request: FastAPI request
        required_scopes: Required scopes

    Returns:
        API key if valid, None otherwise
    """
    api_key_value = get_api_key_from_request(request)

    if not api_key_value:
        return None

    return api_key_manager.validate_api_key(api_key_value, required_scopes)


def require_api_key(scopes: Optional[list] = None):
    """
    Dependency for requiring API key.

    Args:
        scopes: Required scopes

    Returns:
        API key dependency
    """
    async def api_key_dependency(request: Request):
        api_key = await verify_api_key(request, scopes)

        if api_key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key",
                headers={"WWW-Authenticate": "Bearer"}
            )

        return api_key

    return api_key_dependency


def require_api_key_scopes(*scopes: str):
    """
    Dependency for requiring API key with specific scopes.

    Args:
        *scopes: Required scopes

    Returns:
        API key dependency with scope check
    """
    async def api_key_scopes_dependency(request: Request):
        api_key = await verify_api_key(request, list(scopes))

        if api_key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key",
                headers={"WWW-Authenticate": "Bearer"}
            )

        return api_key

    return api_key_scopes_dependency


# API key rate limiter (based on API key rate limit)
def get_api_key_rate_limit(api_key: APIKey) -> int:
    """
    Get rate limit for API key.

    Args:
        api_key: API key object

    Returns:
        Rate limit (requests per minute)
    """
    if api_key:
        return api_key.rate_limit

    return 100  # Default rate limit
