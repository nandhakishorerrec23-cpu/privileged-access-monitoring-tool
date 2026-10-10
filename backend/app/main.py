import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_v1_router
from app.config import settings
from app.database import init_db

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("sentinel")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and models
    logger.info("Initializing database schemas...")
    init_db()
    logger.info("Sentinel backend initialized successfully.")
    yield
    logger.info("Sentinel backend shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    description=f"{settings.APP_SUBTITLE} - Rule-based detection and investigation engine for privileged administrative activity.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security request logging middleware (without exposing raw sensitive payloads)
@app.middleware("http")
async def security_logging_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000

    # Log path, method, status, duration, client IP (avoid logging query secrets or payload)
    client_ip = request.client.host if request.client else "unknown"
    if not request.url.path.startswith("/api/v1/health"):
        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f}ms) [client={client_ip}]"
        )

    return response


# Mount API routes
app.include_router(api_v1_router)

# Mount Frontend static files for single-origin production deployment
frontend_dist_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if frontend_dist_dir.exists() and (frontend_dist_dir / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist_dir / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Do not intercept API or docs routes
        if full_path.startswith("api/") or full_path in ("docs", "redoc", "openapi.json"):
            return None
        target_file = frontend_dist_dir / full_path
        if target_file.exists() and target_file.is_file():
            return FileResponse(target_file)
        return FileResponse(frontend_dist_dir / "index.html")
else:
    @app.get("/")
    def index():
        return {
            "app": settings.APP_NAME,
            "subtitle": settings.APP_SUBTITLE,
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "api_prefix": "/api/v1",
            "frontend_status": "Development mode or build pending. Access Vite dev server on port 5173 or build frontend.",
        }
