"""
API Routes Package

Contains route definitions for API endpoints:
- scan: Skill scanning endpoints
- predict: Risk prediction endpoints
- batch: Batch processing endpoints
- auth: Authentication endpoints
- admin: Admin endpoints
- oauth: OAuth 2.0 endpoints
"""

from .scan import router as scan_router
from .predict import router as predict_router
from .batch import router as batch_router
from .auth import router as auth_router
from .admin import router as admin_router
from .oauth import router as oauth_router

__all__ = [
    'scan_router',
    'predict_router',
    'batch_router',
    'auth_router',
    'admin_router',
    'oauth_router'
]
