"""
API Middleware - Permission Control

RBAC, ABAC, and Scope-based permission control decorators.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import List, Dict, Any, Optional, Union, Callable, Set
from functools import wraps
from enum import Enum
import logging

from ..middleware.auth import verify_token, USERS_DB
from ..middleware.api_key_auth import get_api_key_from_request, api_key_manager

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """Permission definitions."""
    # Admin permissions
    ADMIN_SETTINGS = "admin:settings"
    ADMIN_USERS_MANAGE = "admin:users:manage"
    ADMIN_API_KEYS_MANAGE = "admin:api_keys:manage"
    ADMIN_AUDIT_LOGS = "admin:audit:logs"
    ADMIN_METRICS = "admin:metrics"
    ADMIN_MAINTENANCE = "admin:maintenance"

    # User permissions
    USER_SCAN = "user:scan"
    USER_PREDICT = "user:predict"
    USER_BATCH = "user:batch"
    USER_OWN_KEYS = "user:own_keys"

    # Analyst permissions
    ANALYST_SCAN = "analyst:scan"
    ANALYST_PREDICT = "analyst:predict"
    ANALYST_VIEW_ALL = "analyst:view_all"
    ANALYST_EXPORT = "analyst:export"

    # Viewer permissions
    VIEWER_SCAN = "viewer:scan"
    VIEWER_PREDICT = "viewer:predict"
    VIEWER_VIEW_SELF = "viewer:view_self"


class Role(str, Enum):
    """User roles."""
    ADMIN = "admin"
    USER = "user"
    ANALYST = "analyst"
    VIEWER = "viewer"


class Scope(str, Enum):
    """OAuth 2.0 scopes."""
    OPENID = "openid"
    EMAIL = "email"
    PROFILE = "profile"
    SCAN = "scan"
    PREDICT = "predict"
    BATCH = "batch"
    ADMIN = "admin"


# Role-based access control (RBAC)
ROLE_PERMISSIONS = {
    Role.ADMIN: [
        Permission.ADMIN_SETTINGS,
        Permission.ADMIN_USERS_MANAGE,
        Permission.ADMIN_API_KEYS_MANAGE,
        Permission.ADMIN_AUDIT_LOGS,
        Permission.ADMIN_METRICS,
        Permission.ADMIN_MAINTENANCE,
        Permission.USER_SCAN,
        Permission.USER_PREDICT,
        Permission.USER_BATCH,
        Permission.USER_OWN_KEYS,
        Permission.ANALYST_SCAN,
        Permission.ANALYST_PREDICT,
        Permission.ANALYST_VIEW_ALL,
        Permission.ANALYST_EXPORT,
        Permission.VIEWER_SCAN,
        Permission.VIEWER_PREDICT,
        Permission.VIEWER_VIEW_SELF
    ],
    Role.USER: [
        Permission.USER_SCAN,
        Permission.USER_PREDICT,
        Permission.USER_BATCH,
        Permission.USER_OWN_KEYS
    ],
    Role.ANALYST: [
        Permission.ANALYST_SCAN,
        Permission.ANALYST_PREDICT,
        Permission.ANALYST_VIEW_ALL,
        Permission.ANALYST_EXPORT
    ],
    Role.VIEWER: [
        Permission.VIEWER_SCAN,
        Permission.VIEWER_PREDICT,
        Permission.VIEWER_VIEW_SELF
    ]
}


# Scope-based permissions
SCOPE_PERMISSIONS = {
    Scope.SCAN: [Permission.USER_SCAN, Permission.ANALYST_SCAN, Permission.VIEWER_SCAN],
    Scope.PREDICT: [Permission.USER_PREDICT, Permission.ANALYST_PREDICT, Permission.VIEWER_PREDICT],
    Scope.BATCH: [Permission.USER_BATCH],
    Scope.ADMIN: [
        Permission.ADMIN_SETTINGS,
        Permission.ADMIN_USERS_MANAGE,
        Permission.ADMIN_API_KEYS_MANAGE,
        Permission.ADMIN_AUDIT_LOGS,
        Permission.ADMIN_METRICS,
        Permission.ADMIN_MAINTENANCE
    ]
}


def has_permission(user_role: str, required_permission: Permission) -> bool:
    """
    Check if user has required permission (RBAC).

    Args:
        user_role: User role
        required_permission: Required permission

    Returns:
        True if user has permission, False otherwise
    """
    # Get permissions for role
    role_perms = ROLE_PERMISSIONS.get(Role(user_role), [])

    # Admin has all permissions
    if user_role == Role.ADMIN:
        return True

    # Check if permission is in role permissions
    return required_permission in role_perms


def has_scope_permission(scopes: List[str], required_permission: Permission) -> bool:
    """
    Check if scopes grant required permission.

    Args:
        scopes: List of scopes
        required_permission: Required permission

    Returns:
        True if scopes grant permission, False otherwise
    """
    for scope in scopes:
        scope_perms = SCOPE_PERMISSIONS.get(scope, [])

        if required_permission in scope_perms:
            return True

    return False


def require_permission(required_permission: Permission):
    """
    Decorator to require specific permission.

    Args:
        required_permission: Required permission

    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: Dict = Depends(get_current_user), **kwargs):
            # Get user role
            user_role = current_user.get("role", Role.VIEWER)

            # Check permission
            if not has_permission(user_role, required_permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission required: {required_permission.value}"
                )

            # Call function
            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator


def require_permissions(required_permissions: List[Permission]):
    """
    Decorator to require multiple permissions.

    Args:
        required_permissions: List of required permissions

    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: Dict = Depends(get_current_user), **kwargs):
            # Get user role
            user_role = current_user.get("role", Role.VIEWER)

            # Check all permissions
            for required_permission in required_permissions:
                if not has_permission(user_role, required_permission):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission required: {required_permission.value}"
                    )

            # Call function
            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator


def require_role(required_role: Role):
    """
    Decorator to require specific role.

    Args:
        required_role: Required role

    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: Dict = Depends(get_current_user), **kwargs):
            # Get user role
            user_role = Role(current_user.get("role", Role.VIEWER))

            # Check role
            if user_role != required_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role required: {required_role.value}"
                )

            # Call function
            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator


def require_any_role(required_roles: List[Role]):
    """
    Decorator to require any of specified roles.

    Args:
        required_roles: List of required roles

    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: Dict = Depends(get_current_user), **kwargs):
            # Get user role
            user_role = Role(current_user.get("role", Role.VIEWER))

            # Check if user has any of required roles
            if user_role not in required_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of roles required: {[r.value for r in required_roles]}"
                )

            # Call function
            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator


def require_scope(required_scope: Scope):
    """
    Decorator to require specific OAuth scope.

    Args:
        required_scope: Required scope

    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request, current_user: Dict = Depends(get_current_user), **kwargs):
            # Get user scopes
            user_scopes = current_user.get("scopes", [])

            # Check scope
            if required_scope not in user_scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Scope required: {required_scope.value}"
                )

            # Call function
            return await func(*args, request=request, current_user=current_user, **kwargs)

        return wrapper

    return decorator


def require_any_scope(required_scopes: List[Scope]):
    """
    Decorator to require any of specified OAuth scopes.

    Args:
        required_scopes: List of required scopes

    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request, current_user: Dict = Depends(get_current_user), **kwargs):
            # Get user scopes
            user_scopes = current_user.get("scopes", [])

            # Check if user has any of required scopes
            has_any = any(scope in user_scopes for scope in required_scopes)

            if not has_any:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of scopes required: {[s.value for s in required_scopes]}"
                )

            # Call function
            return await func(*args, request=request, current_user=current_user, **kwargs)

        return wrapper

    return decorator


def require_scope_permission(required_permission: Permission):
    """
    Decorator to require permission via OAuth scopes.

    Args:
        required_permission: Required permission

    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: Dict = Depends(get_current_user), **kwargs):
            # Get user role and scopes
            user_role = current_user.get("role", Role.VIEWER)
            user_scopes = current_user.get("scopes", [])

            # Check RBAC first
            if has_permission(user_role, required_permission):
                # Permission granted via role
                return await func(*args, current_user=current_user, **kwargs)

            # Check scope-based permissions
            if has_scope_permission(user_scopes, required_permission):
                # Permission granted via scope
                return await func(*args, current_user=current_user, **kwargs)

            # Permission not granted
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {required_permission.value}"
            )

        return wrapper

    return decorator


def get_current_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="token"))):
    """
    Get current user from JWT token.

    Args:
        token: JWT access token

    Returns:
        Current user dictionary
    """
    # Verify token
    payload = verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    # Get user
    user_id = payload.get("sub")
    user = None

    for email, user_data in USERS_DB.items():
        if user_data['user_id'] == user_id:
            user = user_data
            break

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


def check_api_key_permissions(api_key_value: str, required_permissions: List[Permission]) -> bool:
    """
    Check if API key has required permissions.

    Args:
        api_key_value: API key value
        required_permissions: List of required permissions

    Returns:
        True if API key has all required permissions, False otherwise
    """
    # Get API key
    api_key = api_key_manager.validate_api_key(api_key_value)

    if not api_key or not api_key.is_valid():
        return False

    # Check scopes
    api_key_scopes = api_key.scopes

    # Check if scopes grant required permissions
    for required_permission in required_permissions:
        # Check if scope grants permission
        if not has_scope_permission(api_key_scopes, required_permission):
            return False

    return True


def require_api_key_permissions(required_permissions: List[Permission]):
    """
    Decorator to require API key permissions.

    Args:
        required_permissions: List of required permissions

    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request):
            # Get API key from request
            api_key_value = get_api_key_from_request(request)

            if not api_key_value:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key required"
                )

            # Check API key permissions
            if not check_api_key_permissions(api_key_value, required_permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"API key does not have required permissions: {[p.value for p in required_permissions]}"
                )

            # Call function
            return await func(*args, api_key=api_key_manager.validate_api_key(api_key_value))

        return wrapper

    return decorator


# Permission inheritance
PERMISSION_HIERARCHY = {
    Permission.ADMIN_USERS_MANAGE: [Permission.ADMIN_SETTINGS],
    Permission.ADMIN_API_KEYS_MANAGE: [Permission.ADMIN_SETTINGS],
    Permission.ADMIN_AUDIT_LOGS: [Permission.ADMIN_SETTINGS],
    Permission.USER_SCAN: [],
    Permission.USER_PREDICT: [Permission.USER_SCAN],
    Permission.USER_BATCH: [Permission.USER_SCAN, Permission.USER_PREDICT],
    Permission.USER_OWN_KEYS: [Permission.USER_SCAN],
    Permission.ANALYST_SCAN: [Permission.USER_SCAN],
    Permission.ANALYST_PREDICT: [Permission.USER_PREDICT],
    Permission.ANALYST_VIEW_ALL: [Permission.ANALYST_SCAN, Permission.ANALYST_PREDICT],
    Permission.ANALYST_EXPORT: [Permission.ANALYST_SCAN, Permission.ANALYST_PREDICT, Permission.ANALYST_VIEW_ALL],
    Permission.VIEWER_SCAN: [Permission.ANALYST_SCAN],
    Permission.VIEWER_PREDICT: [Permission.ANALYST_PREDICT],
    Permission.VIEWER_VIEW_SELF: [Permission.ANALYST_SCAN, Permission.ANALYST_PREDICT]
}


def inherits_permission(parent_permission: Permission, child_permission: Permission) -> bool:
    """
    Check if child permission inherits from parent permission.

    Args:
        parent_permission: Parent permission
        child_permission: Child permission

    Returns:
        True if child inherits from parent, False otherwise
    """
    if parent_permission == child_permission:
        return True

    parent_inherited = PERMISSION_HIERARCHY.get(parent_permission, [])
    return child_permission in parent_inherited


def require_inherited_permissions(parent_permissions: List[Permission]):
    """
    Decorator to require inherited permissions.

    Args:
        parent_permissions: List of parent permissions

    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: Dict = Depends(get_current_user), **kwargs):
            # Get user role
            user_role = current_user.get("role", Role.VIEWER)

            # Check if user has any parent permission
            has_any_parent = False

            for parent_permission in parent_permissions:
                if has_permission(user_role, parent_permission):
                    has_any_parent = True
                    break

            if not has_any_parent:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of parent permissions required: {[p.value for p in parent_permissions]}"
                )

            # Call function
            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator
