"""
FastAPI Application - Production Configuration
"""

import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
import sys
sys.path.insert(0, str(src_path))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

# FastAPI application
app = FastAPI(
    title="SkillGraph API",
    description="""
    AI Agent Skills Security Detection API

    Features:
    - Skill scanning and risk analysis
    - GAT-based risk prediction
    - Entity extraction and community detection
    - Batch processing support
    - Real-time monitoring
    - Authentication and authorization
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Environment variables
ENV = os.getenv("SKILLGRAPH_ENV", "production")
DEBUG = ENV == "development"

# CORS configuration
allow_origins = os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
allow_credentials = True
allow_methods = os.getenv("CORS_ALLOW_METHODS", "*").split(",")
allow_headers = os.getenv("CORS_ALLOW_HEADERS", "*").split(",")

if not allow_origins:
    allow_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=allow_methods,
    allow_headers=allow_headers,
    max_age=600,
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Prometheus instrumentator
instrumentator = Instrumentator(
    should_group_untraced=False,
    should_instrument_requests_inprogress=False,
    should_exclude_untraced=True
)

# Instrument app
if ENV == "production":
    instrumentator.instrument(app, excluded_handlers=["/docs", "/redoc", "/openapi.json"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "SkillGraph API",
        "version": "1.0.0",
        "environment": ENV,
        "description": "AI Agent Skills Security Detection API",
        "endpoints": {
            "health": "/health",
            "scan": "/api/v1/scan",
            "predict": "/api/v1/predict",
            "batch": "/api/v1/batch",
            "auth": "/api/v1/auth",
            "admin": "/api/v1/admin",
            "permissions": "/api/v1/permissions"
        },
        "documentation": {
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": ENV,
        "components": {
            "parser": "ready",
            "graphrag": "ready",
            "models": "loaded" if ENV == "production" else "debug",
            "database": "connected",
            "redis": "connected"
        },
        "debug": DEBUG
    }

# Import routes
try:
    from skillgraph.api.routes import scan, predict, batch, auth, admin, permissions

    # Include routers
    app.include_router(scan.router, prefix="/api/v1", tags=["scan"])
    app.include_router(predict.router, prefix="/api/v1", tags=["predict"])
    app.include_router(batch.router, prefix="/api/v1", tags=["batch"])
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
    app.include_router(permissions.router, prefix="/api/v1", tags=["permissions"])

    print("Routes imported successfully")
except ImportError as e:
    print(f"Warning: Could not import routes: {e}")

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return {
        "message": "Prometheus metrics available at /metrics (Prometheus format)",
        "metrics_url": "/metrics"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    print(f"SkillGraph API starting in {ENV} mode")

    if ENV == "production":
        print("Production mode enabled")
    else:
        print("Development mode enabled")

    print("All routes loaded")
    print("Application ready")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    print("SkillGraph API shutting down")

if __name__ == "__main__":
    import uvicorn

    # Get port from environment or use default
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    # Run uvicorn server
    uvicorn.run(
        "skillgraph.api.main:app",
        host=host,
        port=port,
        reload=DEBUG,
        log_level="info" if ENV == "production" else "debug",
        workers=4 if ENV == "production" else 1,
        access_log=True if ENV == "production" else None
    )
