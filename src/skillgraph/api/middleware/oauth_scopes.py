"""
API Middleware - OAuth 2.0 Scopes

OAuth 2.0 scope management and validation.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import List, Dict, Any, Optional, Set
from enum import Enum
import logging

from .permission import Scope, Permission, has_scope_permission, Role

logger = logging.getLogger(__name__)


class ScopePermission:
    """Scope permission mapping."""

    def __init__(
        self,
        scope: Scope,
        permissions: List[Permission],
        description: str = ""
    ):
        self.scope = scope
        self.permissions = permissions
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'scope': self.scope.value,
            'permissions': [p.value for p in self.permissions],
            'description': self.description
        }


# OAuth 2.0 scope definitions
OAUTH_SCOPES: Dict[str, ScopePermission] = {
    Scope.OPENID: ScopePermission(
        scope=Scope.OPENID,
        permissions=[],
        description="OpenID Connect for authentication"
    ),
    Scope.EMAIL: ScopePermission(
        scope=Scope.EMAIL,
        permissions=[],
        description="Access to user email"
    ),
    Scope.PROFILE: ScopePermission(
        scope=Scope.PROFILE,
        permissions=[],
        description="Access to user profile information"
    ),
    Scope.SCAN: ScopePermission(
        scope=Scope.SCAN,
        permissions=[Permission.USER_SCAN, Permission.ANALYST_SCAN, Permission.VIEWER_SCAN],
        description="Permission to scan skills for security issues"
    ),
    Scope.PREDICT: ScopePermission(
        scope=Scope.PREDICT,
        permissions=[Permission.USER_PREDICT, Permission.ANALYST_PREDICT, Permission.VIEWER_PREDICT],
        description="Permission to predict security risks"
    ),
    Scope.BATCH: ScopePermission(
        scope=Scope.BATCH,
        permissions=[Permission.USER_BATCH, Permission.USER_SCAN],
        description="Permission to perform batch scanning"
    ),
    Scope.ADMIN: ScopePermission(
        scope=Scope.ADMIN,
        permissions=[
            Permission.ADMIN_SETTINGS,
            Permission.ADMIN_USERS_MANAGE,
            Permission.ADMIN_API_KEYS_MANAGE,
            Permission.ADMIN_AUDIT_LOGS,
            Permission.ADMIN_METRICS,
            Permission.ADMIN_MAINTENANCE
        ],
        description="Admin permissions for system management"
    )
}


def get_scope_permissions(scope: Scope) -> ScopePermission:
    """
    Get scope permissions.

    Args:
        scope: OAuth scope

    Returns:
        Scope permission object
    """
    return OAUTH_SCOPES.get(scope)


def validate_scopes(requested_scopes: List[str], role: Optional[Role] = None) -> List[Scope]:
    """
    Validate requested scopes.

    Args:
        requested_scopes: List of requested scopes
        role: User role (optional)

    Returns:
        List of valid scopes
    """
    valid_scopes = []

    for scope_str in requested_scopes:
        # Check if scope exists
        try:
            scope = Scope(scope_str)
        except ValueError:
            continue

        # Check if scope is defined
        if scope not in OAUTH_SCOPES:
            continue

        # Check if user role has access to scope
        if role:
            scope_perms = OAUTH_SCOPES[scope].permissions
            role_perms = []

            # Get role permissions
            from .permission import ROLE_PERMISSIONS

            if Role(role) in ROLE_PERMISSIONS:
                role_perms = ROLE_PERMISSIONS[Role(role)]

            # Check if role has any scope permission
            has_any_perm = any(perm in role_perms for perm in scope_perms)

            if not has_any_perm:
                continue

        valid_scopes.append(scope)

    return valid_scopes


def check_scope_permissions(user_scopes: List[str], required_permissions: List[Permission]) -> bool:
    """
    Check if user scopes grant required permissions.

    Args:
        user_scopes: List of user scopes
        required_permissions: List of required permissions

    Returns:
        True if scopes grant all required permissions, False otherwise
    """
    for required_permission in required_permissions:
        # Check if any scope grants permission
        has_perm = has_scope_permission(user_scopes, required_permission)

        if not has_perm:
            return False

    return True


def get_all_scopes() -> List[Dict[str, Any]]:
    """
    Get all available scopes.

    Returns:
        List of scope definitions
    """
    scopes = []

    for scope, perm_obj in OAUTH_SCOPES.items():
        scopes.append(perm_obj.to_dict())

    return scopes


def get_scope_for_permission(permission: Permission) -> Optional[Scope]:
    """
    Get scope that grants permission.

    Args:
        permission: Required permission

    Returns:
        Scope that grants permission, or None
    """
    for scope, scope_perm in OAUTH_SCOPES.items():
        if permission in scope_perm.permissions:
            return scope

    return None


def get_permissions_for_scope(scope: Scope) -> List[Permission]:
    """
    Get permissions for scope.

    Args:
        scope: OAuth scope

    Returns:
        List of permissions granted by scope
    """
    scope_perm = OAUTH_SCOPES.get(scope)

    if not scope_perm:
        return []

    return scope_perm.permissions


def get_scopes_for_role(role: Role) -> List[Scope]:
    """
    Get scopes available for role.

    Args:
        role: User role

    Returns:
        List of scopes available to role
    """
    # Get role permissions
    from .permission import ROLE_PERMISSIONS
    role_perms = ROLE_PERMISSIONS.get(role, [])

    # Find scopes that grant role permissions
    available_scopes = []

    for scope, scope_perm in OAUTH_SCOPES.items():
        # Check if scope grants any role permission
        has_any_perm = any(perm in role_perms for perm in scope_perm.permissions)

        if has_any_perm:
            available_scopes.append(scope)

    return available_scopes


# OAuth 2.0 scope validation middleware
def require_oauth_scopes(required_scopes: List[Scope]):
    """
    Decorator to require specific OAuth scopes.

    Args:
        required_scopes: List of required scopes

    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: Dict = Depends(get_current_user), **kwargs):
            # Get user scopes
            user_scopes = current_user.get("scopes", [])

            # Check if user has all required scopes
            has_all = all(scope.value in user_scopes for scope in required_scopes)

            if not has_all:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Scopes required: {[s.value for s in required_scopes]}"
                )

            # Call function
            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator


def require_any_oauth_scope(required_scopes: List[Scope]):
    """
    Decorator to require any of specified OAuth scopes.

    Args:
        required_scopes: List of required scopes

    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: Dict = Depends(get_current_user), **kwargs):
            # Get user scopes
            user_scopes = current_user.get("scopes", [])

            # Check if user has any of required scopes
            has_any = any(scope.value in user_scopes for scope in required_scopes)

            if not has_any:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of scopes required: {[s.value for s in required_scopes]}"
                )

            # Call function
            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator


# Export all functions
__all__ = [
    'Scope',
    'Permission',
    'Role',
    'OAUTH_SCOPES',
    'get_scope_permissions',
    'validate_scopes',
    'check_scope_permissions',
    'get_all_scopes',
    'get_scope_for_permission',
    'get_permissions_for_scope',
    'get_scopes_for_role',
    'require_oauth_scopes',
    'require_any_oauth_scope',
    'require_permission',
    'require_permissions',
    'require_role',
    'require_any_role',
    'require_scope',
    'require_any_scope',
    'require_scope_permission',
    'require_api_key_permissions',
    'get_current_user',
    'check_api_key_permissions'
]
