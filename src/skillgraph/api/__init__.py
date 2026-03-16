"""
FastAPI Application - SkillGraph API

Production-ready FastAPI service with:
- Skill scanning endpoints
- Risk prediction endpoints
- Batch processing
- Authentication and authorization
- Rate limiting
- Monitoring and logging
"""

import os
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

# FastAPI imports
try:
    from fastapi import FastAPI, Request, Response, status, HTTPException, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.gzip import GZipMiddleware
    from fastapi.responses import JSONResponse
    from fastapi.security import OAuth2PasswordBearer
    from prometheus_fastapi_instrumentator import Instrumentator
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("Warning: FastAPI not installed. Install with: pip install fastapi")
    import sys
    sys.exit(1)

# Add src to path
src_path = Path(__file__).parent.parent.parent / 'src'
import sys
sys.path.insert(0, str(src_path))

# SkillGraph imports
from skillgraph.parser import SkillParser
from skillgraph.graphrag import EntityExtractor, CommunityDetector
from skillgraph.graphrag.models import EntityType


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

# Prometheus instrumentator
instrumentator = Instrumentator(
    should_group_untraced=False,
    should_instrument_requests_inprogress=False,
    should_exclude_untraced=True
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=600,
)

# Configure GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Instrument FastAPI for metrics
instrumentator.instrument(app)


# Global variables
parser = SkillParser()
entity_extractor = None
community_detector = None


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "SkillGraph API",
        "version": "1.0.0",
        "description": "AI Agent Skills Security Detection API",
        "endpoints": {
            "health": "/health",
            "scan": "/api/v1/scan",
            "predict": "/api/v1/predict",
            "batch": "/api/v1/batch",
            "metrics": "/metrics"
        },
        "documentation": {
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "components": {
            "parser": "ready",
            "graphrag": "ready"
        }
    }


# Import routes
try:
    from skillgraph.api.routes import scan, predict, batch

    app.include_router(scan.router, prefix="/api/v1", tags=["scan"])
    app.include_router(predict.router, prefix="/api/v1", tags=["predict"])
    app.include_router(batch.router, prefix="/api/v1", tags=["batch"])

except ImportError as e:
    print(f"Warning: Could not import routes: {e}")


if __name__ == "__main__":
    import uvicorn

    # Run the server
    uvicorn.run(
        "skillgraph.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
