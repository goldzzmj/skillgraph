"""
API Routes - Authentication Endpoints

Authentication and authorization endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from typing import Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt

from ..models import UserLogin, UserResponse, UserCreate

router = APIRouter(prefix="/api/v1", tags=["auth"])

# JWT configuration
JWT_SECRET = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Mock user database (in production, use real database)
USERS_DB = {
    "admin@skillgraph.com": {
        "user_id": "admin_001",
        "email": "admin@skillgraph.com",
        "password_hash": pwd_context.hash("admin123"),
        "role": "admin",
        "full_name": "Admin User"
    },
    "user@skillgraph.com": {
        "user_id": "user_001",
        "email": "user@skillgraph.com",
        "password_hash": pwd_context.hash("user123"),
        "role": "user",
        "full_name": "Regular User"
    }
}


@router.post("/auth/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    """
    Register new user.

    Args:
        user_data: User creation request

    Returns:
        UserResponse with access token
    """
    # Check if user already exists
    if user_data.email in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user (in production, save to database)
    user = {
        "user_id": f"user_{user_data.email.split('@')[0]}",
        "email": user_data.email,
        "password_hash": pwd_context.hash(user_data.password),
        "role": user_data.role,
        "full_name": user_data.full_name
    }

    # Add to mock database
    USERS_DB[user_data.email] = user

    # Create tokens
    access_token = create_access_token({
        "sub": user['user_id'],
        "email": user['email'],
        "role": user['role']
    })

    refresh_token = create_refresh_token({
        "sub": user['user_id'],
        "email": user['email']
    })

    return UserResponse(
        user_id=user['user_id'],
        email=user['email'],
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        full_name=user['full_name'],
        role=user['role'],
        expires_in=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/auth/login", response_model=UserResponse)
async def login(user_credentials: UserLogin):
    """
    User login.

    Args:
        user_credentials: User login request

    Returns:
        UserResponse with access token
    """
    # Check if user exists
    if user_credentials.email not in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    user = USERS_DB[user_credentials.email]

    # Verify password
    if not pwd_context.verify(user_credentials.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Create tokens
    access_token = create_access_token({
        "sub": user['user_id'],
        "email": user['email'],
        "role": user['role']
    })

    refresh_token = create_refresh_token({
        "sub": user['user_id'],
        "email": user['email']
    })

    return UserResponse(
        user_id=user['user_id'],
        email=user['email'],
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        full_name=user['full_name'],
        role=user['role'],
        expires_in=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/auth/refresh", response_model=UserResponse)
async def refresh_token(refresh_token: str = Body(..., embed=True)):
    """
    Refresh access token.

    Args:
        refresh_token: Refresh token

    Returns:
        UserResponse with new access token
    """
    try:
        # Decode refresh token
        payload = jwt.decode(
            refresh_token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )

        user_id = payload.get("sub")

        # Get user
        user = None
        for email, user_data in USERS_DB.items():
            if user_data['user_id'] == user_id:
                user = user_data
                break

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Create new access token
        access_token = create_access_token({
            "sub": user['user_id'],
            "email": user['email'],
            "role": user['role']
        })

        return UserResponse(
            user_id=user['user_id'],
            email=user['email'],
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            full_name=user['full_name'],
            role=user['role'],
            expires_in=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.get("/auth/me")
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get current user info.

    Args:
        token: Access token

    Returns:
        User info
    """
    try:
        # Decode token
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )

        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role")

        # Get user
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

        return {
            "user_id": user['user_id'],
            "email": user['email'],
            "full_name": user['full_name'],
            "role": user['role']
        }

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def create_access_token(data: dict) -> str:
    """Create access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt
