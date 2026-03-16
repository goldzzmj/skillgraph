"""SkillGraph API route modules."""

from .scan import router as scan_router
from .predict import router as predict_router
from .batch import router as batch_router
from .auth import router as auth_router
from .admin import router as admin_router
from .permissions import router as permissions_router

__all__ = [
    'scan_router',
    'predict_router',
    'batch_router',
    'auth_router',
    'admin_router',
    'permissions_router'
]
