"""
API Routes - Permissions

Permission management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import List, Dict, Any

from ..middleware.permission import (
    Permission,
    Role,
    Scope,
    get_all_scopes,
    get_permissions_for_scope,
    get_scopes_for_role,
    require_permission,
    require_any_permission,
    require_role,
    require_any_role,
    get_current_user
)

router = APIRouter(prefix="/api/v1", tags=["permissions"])

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.get("/permissions", response_model=List[Dict[str, Any]])
async def get_all_permissions(current_user: Dict = Depends(get_current_user)):
    """
    Get all available permissions (admin only).

    Args:
        current_user: Current user (must be admin)

    Returns:
        List of all permissions
    """
    # Check if user is admin
    if current_user.get("role") != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )

    # Return all permissions
    permissions = [
        {
            'permission': perm.value,
            'description': perm.value.replace(':', ' ').title()
        }
        for perm in Permission
    ]

    return permissions


@router.get("/roles", response_model=List[Dict[str, Any]])
async def get_all_roles(current_user: Dict = Depends(get_current_user)):
    """
    Get all available roles (admin only).

    Args:
        current_user: Current user (must be admin)

    Returns:
        List of all roles
    """
    # Check if user is admin
    if current_user.get("role") != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )

    # Return all roles
    roles = []

    for role in Role:
        # Get scopes for role
        scopes = get_scopes_for_role(role)

        # Get permissions for role
        from ..middleware.permission import ROLE_PERMISSIONS
        role_perms = ROLE_PERMISSIONS.get(role, [])

        roles.append({
            'role': role.value,
            'description': role.value.capitalize(),
            'scopes': [s.value for s in scopes],
            'permissions': [p.value for p in role_perms]
        })

    return roles


@router.get("/scopes", response_model=List[Dict[str, Any]])
async def get_all_scopes(current_user: Dict = Depends(get_current_user)):
    """
    Get all available scopes.

    Args:
        current_user: Current user

    Returns:
        List of all scopes
    """
    from ..middleware.oauth_scopes import get_all_scopes as get_all_oauth_scopes

    # Get all OAuth scopes
    oauth_scopes = get_all_oauth_scopes()

    return oauth_scopes


@router.get("/scopes/{scope_name}", response_model=Dict[str, Any]])
async def get_scope_info(
    scope_name: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get scope information.

    Args:
        scope_name: Scope name
        current_user: Current user

    Returns:
        Scope information
    """
    try:
        scope = Scope(scope_name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scope: {scope_name}"
        )

    # Get scope permissions
    from ..middleware.oauth_scopes import get_scope_permissions, get_scope_for_permission

    scope_perm = get_scope_permissions(scope)

    if not scope_perm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scope not found: {scope_name}"
        )

    # Get permissions for scope
    permissions = [
        perm.value for perm in scope_perm.permissions
    ]

    return {
        'scope': scope.value,
        'description': scope_perm.description,
        'permissions': permissions
    }


@router.get("/roles/{role_name}/scopes", response_model=List[Dict[str, Any]])
async def get_scopes_for_role_endpoint(
    role_name: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get scopes available for role.

    Args:
        role_name: Role name
        current_user: Current user

    Returns:
        List of scopes available for role
    """
    # Get role
    try:
        role = Role(role_name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {role_name}"
        )

    # Get scopes for role
    scopes = get_scopes_for_role(role)

    return [
        {
            'scope': scope.value,
            'description': scope.value.capitalize()
        }
        for scope in scopes
    ]


@router.get("/roles/{role_name}/permissions", response_model=List[Dict[str, Any]])
async def get_permissions_for_role_endpoint(
    role_name: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get permissions for role.

    Args:
        role_name: Role name
        current_user: Current user

    Returns:
        List of permissions for role
    """
    # Get role
    try:
        role = Role(role_name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {role_name}"
        )

    # Get permissions for role
    from ..middleware.permission import ROLE_PERMISSIONS

    role_perms = ROLE_PERMISSIONS.get(role, [])

    return [
        {
            'permission': perm.value,
            'description': perm.value.replace(':', ' ').title()
        }
        for perm in role_perms
    ]


@router.get("/users/me/permissions", response_model=List[Dict[str, Any]])
async def get_user_permissions(current_user: Dict = Depends(get_current_user)):
    """
    Get user's permissions.

    Args:
        current_user: Current user

    Returns:
        List of user's permissions
    """
    # Get user role
    user_role = current_user.get("role", Role.VIEWER)

    # Get scopes for role
    scopes = get_scopes_for_role(user_role)

    # Get permissions from scopes
    from ..middleware.oauth_scopes import get_permissions_for_scope

    permissions = []

    for scope in scopes:
        scope_perms = get_permissions_for_scope(scope)
        permissions.extend(scope_perms)

    # Remove duplicates
    permissions = list(set(permissions))

    # Get permissions from role
    from ..middleware.permission import ROLE_PERMISSIONS
    role_perms = ROLE_PERMISSIONS.get(user_role, [])
    permissions.extend(role_perms)

    # Remove duplicates
    permissions = list(set(permissions))

    return [
        {
            'permission': perm,
            'description': perm.replace(':', ' ').title()
        }
        for perm in sorted(permissions)
    ]


@router.get("/users/me/scopes", response_model=List[Dict[str, Any]])
async def get_user_scopes(current_user: Dict = Depends(get_current_user)):
    """
    Get user's scopes.

    Args:
        current_user: Current user

    Returns:
        List of user's scopes
    """
    # Get user role
    user_role = current_user.get("role", Role.VIEWER)

    # Get scopes for role
    scopes = get_scopes_for_role(user_role)

    # Add OAuth scopes if any
    user_oauth_scopes = current_user.get("scopes", [])

    # Merge scopes
    all_scopes = list(set([s.value for s in scopes] + user_oauth_scopes))

    return [
        {
            'scope': scope,
            'description': scope.capitalize()
        }
        for scope in sorted(all_scopes)
    ]
