"""
API Routes - OAuth 2.0

OAuth 2.0 authorization endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2AuthorizationCodeBearer
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import secrets
import urllib.parse

from jose import JWTError, jwt

from ..models import UserResponse
from ..middleware import AuthenticationError
from ..middleware.auth import (
    verify_token,
    create_access_token,
    create_refresh_token,
    USERS_DB,
    pwd_context
)

router = APIRouter(prefix="/api/v1/auth", tags=["oauth"])

# OAuth 2.0 configuration
OAUTH_CLIENT_ID = "skillgraph-client"
OAUTH_CLIENT_SECRET = "skillgraph-secret-change-in-production"
OAUTH_REDIRECT_URI = "http://localhost:8000/oauth/callback"
OAUTH_SCOPE = "openid email profile"
OAUTH_TOKEN_EXPIRE_SECONDS = 3600  # 1 hour
OAUTH_REFRESH_TOKEN_EXPIRE_DAYS = 30
OAUTH_CODE_EXPIRE_SECONDS = 600  # 10 minutes

# OAuth2 authorization code bearer
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    tokenUrl="token",
    authorizationUrl="https://accounts.example.com/authorize",
    tokenUrl="https://accounts.example.com/oauth/access_token",
    refreshUrl="https://accounts.example.com/oauth/token",
    scopes=OAUTH_SCOPE,
    auto_error=False
)

# Mock authorization codes database
AUTH_CODES_DB: Dict[str, Dict[str, Any]] = {}


def generate_authorization_code(user_id: str, expires_in_seconds: int = 600) -> Dict[str, Any]:
    """Generate OAuth 2.0 authorization code."""
    code = secrets.token_urlsafe(32)

    auth_code_data = {
        "code": code,
        "user_id": user_id,
        "client_id": OAUTH_CLIENT_ID,
        "redirect_uri": OAUTH_REDIRECT_URI,
        "scope": OAUTH_SCOPE,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(seconds=expires_in_seconds),
        "is_used": False
    }

    # Store authorization code
    AUTH_CODES_DB[code] = auth_code_data

    return auth_code_data


def verify_authorization_code(code: str, client_id: str, redirect_uri: str) -> Dict[str, Any]:
    """Verify OAuth 2.0 authorization code."""
    auth_code_data = AUTH_CODES_DB.get(code)

    if not auth_code_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid authorization code"
        )

    # Check if code is expired
    if datetime.utcnow() > auth_code_data['expires_at']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code expired"
        )

    # Check if code is already used
    if auth_code_data['is_used']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code already used"
        )

    # Check client ID
    if auth_code_data['client_id'] != client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client ID"
        )

    # Check redirect URI
    if auth_code_data['redirect_uri'] != redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid redirect URI"
        )

    # Mark code as used
    auth_code_data['is_used'] = True
    AUTH_CODES_DB[code] = auth_code_data

    return auth_code_data


@router.get("/authorize")
async def oauth_authorize(
    response_type: str = "code",
    client_id: str = None,
    redirect_uri: str = None,
    scope: Optional[str] = None,
    state: Optional[str] = None,
    login_hint: Optional[str] = None
):
    """
    OAuth 2.0 authorization endpoint.

    Args:
        response_type: Must be "code"
        client_id: Client ID
        redirect_uri: Redirect URI
        scope: Requested scopes
        state: State parameter
        login_hint: Preferred login user

    Returns:
        Redirects to login page if user not authenticated
    """
    # Validate parameters
    if response_type != "code":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="response_type must be 'code'"
        )

    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="client_id is required"
        )

    if not redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="redirect_uri is required"
        )

    # Validate client_id
    if client_id != OAUTH_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client_id"
        )

    # Validate redirect_uri
    if redirect_uri != OAUTH_REDIRECT_URI:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid redirect_uri"
        )

    # In production, check if user is authenticated
    # If not, redirect to login page with parameters
    login_page_url = f"/login?client_id={client_id}&redirect_uri={urllib.parse.quote(redirect_uri)}&response_type=code"

    if scope:
        login_page_url += f"&scope={urllib.parse.quote(scope)}"

    if state:
        login_page_url += f"&state={urllib.parse.quote(state)}"

    if login_hint:
        login_page_url += f"&login_hint={urllib.parse.quote(login_hint)}"

    return {
        "message": "Redirect to login page",
        "login_page_url": login_page_url,
        "status": "login_required",
        "params": {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": response_type,
            "scope": scope,
            "state": state
        }
    }


@router.post("/token")
async def oauth_token(
    grant_type: str = Body(..., embed=True),
    code: Optional[str] = Body(None),
    redirect_uri: Optional[str] = Body(None),
    client_id: Optional[str] = Body(None),
    client_secret: Optional[str] = Body(None),
    refresh_token: Optional[str] = Body(None),
    scope: Optional[str] = Body(None)
):
    """
    OAuth 2.0 token endpoint.

    Args:
        grant_type: Grant type (authorization_code or refresh_token)
        code: Authorization code
        redirect_uri: Redirect URI
        client_id: Client ID
        client_secret: Client secret
        refresh_token: Refresh token
        scope: Requested scopes

    Returns:
        OAuth 2.0 token response
    """
    # Handle authorization code grant
    if grant_type == "authorization_code":
        # Validate parameters
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="code is required for authorization_code grant type"
            )

        if not client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="client_id is required for authorization_code grant type"
            )

        if not client_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="client_secret is required for authorization_code grant type"
            )

        # Validate client credentials
        if client_id != OAUTH_CLIENT_ID or client_secret != OAUTH_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid client credentials"
            )

        # Verify authorization code
        auth_code_data = verify_authorization_code(
            code=code,
            client_id=client_id,
            redirect_uri=redirect_uri or OAUTH_REDIRECT_URI
        )

        # Get user from authorization code
        user_id = auth_code_data['user_id']
        user = None

        for email, user_data in USERS_DB.items():
            if user_data['user_id'] == user_id:
                user = user_data
                break

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}"
            )

        # Generate access token
        access_token_payload = {
            "sub": user['user_id'],
            "email": user['email'],
            "role": user['role'],
            "scope": scope or OAUTH_SCOPE,
            "client_id": client_id,
            "grant_type": "authorization_code"
        }

        access_token = create_access_token(access_token_payload)
        refresh_token = create_refresh_token({
            "sub": user['user_id'],
            "email": user['email'],
            "client_id": client_id
        })

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": OAUTH_TOKEN_EXPIRE_SECONDS,
            "refresh_token": refresh_token,
            "scope": scope or OAUTH_SCOPE
        }

    # Handle refresh token grant
    elif grant_type == "refresh_token":
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="refresh_token is required for refresh_token grant type"
            )

        if not client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="client_id is required for refresh_token grant type"
            )

        # Validate refresh token
        try:
            payload = verify_token(refresh_token)

            # Validate client_id
            if payload.get("client_id") != client_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid client_id in refresh token"
                )

            # Get user from refresh token
            user_id = payload.get("sub")
            user = None

            for email, user_data in USERS_DB.items():
                if user_data['user_id'] == user_id:
                    user = user_data
                    break

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User not found: {user_id}"
                )

            # Generate new access token
            access_token_payload = {
                "sub": user['user_id'],
                "email": user['email'],
                "role": user['role'],
                "scope": payload.get("scope", OAUTH_SCOPE),
                "client_id": client_id,
                "grant_type": "refresh_token"
            }

            access_token = create_access_token(access_token_payload)

            return {
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": OAUTH_TOKEN_EXPIRE_SECONDS,
                "scope": payload.get("scope", OAUTH_SCOPE)
            }

        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid refresh token: {str(e)}"
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported grant_type: {grant_type}"
        )


@router.get("/userinfo")
async def oauth_userinfo(
    token: str = Depends(oauth2_scheme)
):
    """
    OAuth 2.0 userinfo endpoint.

    Args:
        token: Access token

    Returns:
        User information
    """
    try:
        payload = verify_token(token)

        # Get user from payload
        user_id = payload.get("sub")
        user = None

        for email, user_data in USERS_DB.items():
            if user_data['user_id'] == user_id:
                user = user_data
                break

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}"
            )

        # Return user info
        return {
            "sub": user['user_id'],
            "name": user['full_name'],
            "given_name": user['full_name'].split()[0],
            "family_name": user['full_name'].split()[-1],
            "email": user['email'],
            "email_verified": True,
            "picture": f"https://api.dicebear.com/7.x/{user['email']}.png",
            "role": user['role'],
            "preferred_username": user['user_id'],
            "updated_at": user.get('updated_at', datetime.utcnow().isoformat())
        }

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


@router.post("/logout")
async def oauth_logout(
    token: str = Body(..., embed=True),
    token_type_hint: str = "access_token"
):
    """
    OAuth 2.0 logout endpoint.

    Args:
        token: Token to revoke
        token_type_hint: Token type (access_token or refresh_token)

    Returns:
        Logout result
    """
    # In production, add token to revocation list
    # For now, just return success

    return {
        "message": "Logout successful",
        "token_type": token_type_hint,
        "revoked_at": datetime.utcnow().isoformat()
    }
