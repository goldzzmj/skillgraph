"""FastAPI entrypoint for local SkillGraph API startup."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from skillgraph.api.routes.batch import router as batch_router
from skillgraph.api.routes.predict import router as predict_router
from skillgraph.api.routes.scan import router as scan_router
from skillgraph.graphstore import routes as graph_routes

__version__ = "1.0.0"


app = FastAPI(
    title="SkillGraph API",
    description="AI Agent Skills Security Detection API",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "name": "SkillGraph API",
        "version": __version__,
        "health": "/health",
        "docs": "/docs",
    }


@app.get("/health")
async def health() -> dict:
    """Health endpoint."""
    return {"status": "healthy", "version": __version__}


# Keep current route modules as-is and register with compatible prefixes.
app.include_router(scan_router, prefix="/api/v1")
app.include_router(predict_router)
app.include_router(batch_router)
app.include_router(graph_routes.router)
