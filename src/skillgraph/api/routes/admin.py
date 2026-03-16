"""
API Routes - Admin Endpoints

Admin endpoints for user and API key management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

from ..models import UserCreate, UserResponse
from ..middleware import (
    AuthenticationError,
    AuthorizationError,
    APIKey,
    api_key_manager,
    get_api_key_rate_limit
)
from ..dependencies import get_async_db

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def require_admin():
    """Decorator to require admin role."""
    async def admin_checker(token: str = Depends(oauth2_scheme)):
        # Verify token
        from ..middleware.auth import verify_token

        payload = verify_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        # Check admin role
        user_role = payload.get("role")
        if user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required"
            )

        return payload

    return admin_checker


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(admin_payload: Dict = Depends(require_admin)):
    """
    Get all users (admin only).

    Args:
        admin_payload: Admin token payload

    Returns:
        List of all users
    """
    # Get all users from mock database
    from ..middleware.auth import USERS_DB

    users = []

    for email, user_data in USERS_DB.items():
        user_response = UserResponse(
            user_id=user_data['user_id'],
            email=email,
            access_token="",  # Don't return access token
            refresh_token="",  # Don't return refresh token
            token_type="Bearer",
            full_name=user_data['full_name'],
            role=user_data['role']
        )
        users.append(user_response)

    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_details(
    user_id: str,
    admin_payload: Dict = Depends(require_admin)
):
    """
    Get user details by ID (admin only).

    Args:
        user_id: User ID
        admin_payload: Admin token payload

    Returns:
        User details
    """
    # Get user from database
    from ..middleware.auth import USERS_DB

    for email, user_data in USERS_DB.items():
        if user_data['user_id'] == user_id:
            return UserResponse(
                user_id=user_data['user_id'],
                email=email,
                access_token="",
                refresh_token="",
                token_type="Bearer",
                full_name=user_data['full_name'],
                role=user_data['role']
            )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"User not found: {user_id}"
    )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin_payload: Dict = Depends(require_admin)
):
    """
    Delete user (admin only).

    Args:
        user_id: User ID
        admin_payload: Admin token payload

    Returns:
        Deletion result
    """
    # Delete user from database
    from ..middleware.auth import USERS_DB

    user_deleted = False
    user_email = None

    for email, user_data in list(USERS_DB.items()):
        if user_data['user_id'] == user_id:
            del USERS_DB[email]
            user_deleted = True
            user_email = email
            break

    if not user_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}"
        )

    return {
        "message": f"User deleted: {user_id}",
        "user_email": user_email,
        "deleted_at": datetime.utcnow().isoformat()
    }


@router.get("/api-keys", response_model=List[Dict[str, Any]])
async def get_all_api_keys(admin_payload: Dict = Depends(require_admin)):
    """
    Get all API keys (admin only).

    Args:
        admin_payload: Admin token payload

    Returns:
        List of all API keys
    """
    # Get all API keys from database
    api_keys = []

    for key_value, api_key in api_key_manager.get_api_keys_by_owner(None).items():
        # In production, filter by owner
        api_key_info = api_key.to_dict()
        api_keys.append(api_key_info)

    return api_keys


@router.delete("/api-keys/{key_value}")
async def revoke_api_key(
    key_value: str,
    admin_payload: Dict = Depends(require_admin)
):
    """
    Revoke API key (admin only).

    Args:
        key_value: API key value
        admin_payload: Admin token payload

    Returns:
        Revocation result
    """
    # Revoke API key
    revoked = api_key_manager.revoke_api_key(key_value)

    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key not found: {key_value}"
        )

    return {
        "message": f"API key revoked: {key_value}",
        "revoked_at": datetime.utcnow().isoformat()
    }


@router.post("/api-keys", response_model=Dict[str, Any])
async def create_api_key_for_user(
    user_id: str,
    key_data: Optional[Dict[str, Any]] = None,
    admin_payload: Dict = Depends(require_admin)
):
    """
    Create API key for user (admin only).

    Args:
        user_id: User ID
        key_data: API key data
        admin_payload: Admin token payload

    Returns:
        Created API key
    """
    # Extract key data
    name = key_data.get('name', f"API Key for {user_id}")
    scopes = key_data.get('scopes', ['scan', 'predict'])
    rate_limit = key_data.get('rate_limit', 1000)
    expires_days = key_data.get('expires_days', 365)

    # Generate API key
    api_key = api_key_manager.generate_api_key(
        name=name,
        scopes=scopes,
        rate_limit=rate_limit,
        expires_days=expires_days,
        owner_id=user_id
    )

    return {
        "message": "API key created successfully",
        "api_key": api_key.key_value,
        "key_id": api_key.key_id,
        "name": api_key.name,
        "scopes": api_key.scopes,
        "rate_limit": api_key.rate_limit,
        "is_active": api_key.is_active,
        "created_at": api_key.created_at.isoformat(),
        "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
        "owner_id": api_key.owner_id
    }


@router.get("/stats")
async def get_system_stats(admin_payload: Dict = Depends(require_admin)):
    """
    Get system statistics (admin only).

    Args:
        admin_payload: Admin token payload

    Returns:
        System statistics
    """
    # Get system statistics
    from ..middleware.auth import USERS_DB

    stats = {
        "total_users": len(USERS_DB),
        "total_api_keys": len([k for k in api_key_manager.USERS_DB.keys() if k.is_active]),
        "system_status": "healthy",
        "api_version": "1.0.0",
        "uptime_seconds": 3600,  # In production, calculate actual uptime
        "requests_today": 1500,  # In production, get actual count
        "active_sessions": 25  # In production, get actual count
    }

    return stats


@router.get("/audit/logs")
async def get_audit_logs(
    limit: int = 100,
    admin_payload: Dict = Depends(require_admin)
):
    """
    Get audit logs (admin only).

    Args:
        limit: Number of logs to return
        admin_payload: Admin token payload

    Returns:
        Audit logs
    """
    # Get audit logs
    # In production, get from audit log database
    audit_logs = []

    # Mock audit logs
    import random

    for i in range(limit):
        action_types = ['user_login', 'api_key_create', 'scan_request', 'admin_action', 'user_delete']
        users = ['user_001', 'user_002', 'user_003', 'admin_001']

        log = {
            "log_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "action": random.choice(action_types),
            "user_id": random.choice(users),
            "ip_address": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "status_code": random.choice([200, 201, 204, 400, 401, 403, 500]),
            "success": random.choice([True, True, True, False])
        }

        audit_logs.append(log)

    return {
        "logs": audit_logs,
        "total": len(audit_logs),
        "returned": len(audit_logs)
    }


@router.get("/metrics")
async def get_api_metrics(admin_payload: Dict = Depends(require_admin)):
    """
    Get API metrics (admin only).

    Args:
        admin_payload: Admin token payload

    Returns:
        API metrics
    """
    # Get API metrics
    # In production, get from Prometheus or metrics database
    metrics = {
        "total_requests": 15000,
        "successful_requests": 14500,
        "failed_requests": 500,
        "average_response_time_ms": 85.5,
        "requests_per_minute": 60,
        "requests_per_hour": 3600,
        "peak_concurrent_requests": 25,
        "active_users": 15,
        "active_api_keys": 10,
        "high_risk_scans": 150,
        "medium_risk_scans": 300,
        "low_risk_scans": 600
    }

    return metrics


@router.post("/maintenance")
async def enable_maintenance_mode(
    enabled: bool = True,
    message: str = "System under maintenance",
    admin_payload: Dict = Depends(require_admin)
):
    """
    Enable or disable maintenance mode (admin only).

    Args:
        enabled: Whether to enable maintenance mode
        message: Maintenance message
        admin_payload: Admin token payload

    Returns:
        Maintenance status
    """
    # In production, set maintenance flag in database or configuration
    # For now, just return status

    return {
        "maintenance_enabled": enabled,
        "message": message,
        "set_at": datetime.utcnow().isoformat(),
        "set_by": admin_payload.get('sub', 'unknown')
    }


@router.get("/users/{user_id}/activity")
async def get_user_activity(
    user_id: str,
    days: int = 30,
    admin_payload: Dict = Depends(require_admin)
):
    """
    Get user activity (admin only).

    Args:
        user_id: User ID
        days: Number of days to look back
        admin_payload: Admin token payload

    Returns:
        User activity
    """
    # Get user activity
    # In production, get from activity log database
    activity = []

    start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days)

    for i in range(days):
        date = start_date + timedelta(days=i)

        day_activity = {
            "date": date.strftime("%Y-%m-%d"),
            "login_count": random.randint(0, 10),
            "scan_count": random.randint(0, 20),
            "batch_count": random.randint(0, 5),
            "api_calls": random.randint(10, 50),
            "failed_attempts": random.randint(0, 2)
        }

        activity.append(day_activity)

    # Calculate summary
    total_logins = sum(day['login_count'] for day in activity)
    total_scans = sum(day['scan_count'] for day in activity)
    total_api_calls = sum(day['api_calls'] for day in activity)

    return {
        "user_id": user_id,
        "activity_period": f"{days} days",
        "activity": activity,
        "summary": {
            "total_logins": total_logins,
            "total_scans": total_scans,
            "total_api_calls": total_api_calls,
            "average_daily_logins": total_logins / days if days > 0 else 0,
            "average_daily_scans": total_scans / days if days > 0 else 0,
            "average_daily_api_calls": total_api_calls / days if days > 0 else 0
        }
    }
