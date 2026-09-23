# backend/src/main.py

import logging
import sys
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram, Gauge

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from src.db.database import check_db_connection, close_db
from src.db.init_db import initialize_database
from src.routers import auth, returns, kam, batch, kpi, reports, control_tower, admin, decision, dropoff, pickup

logger = logging.getLogger(__name__)

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"]
)

ACTIVE_REQUESTS = Gauge(
    "http_requests_active",
    "Number of active HTTP requests"
)

APP_VERSION = "1.0.0"
SERVICE_NAME = "logistica-inversa-api"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Sistema Inteligente de Logistica Inversa API...")

    try:
        await initialize_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    yield

    logger.info("Shutting down...")
    await close_db()
    logger.info("Shutdown complete")


def get_application() -> FastAPI:
    application = FastAPI(
        title=settings.api.API_TITLE,
        description="API RESTful para la gestion inteligente de devoluciones y logistica inversa",
        version=APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    cors_origins = settings.security.CORS_ORIGINS.split(",")

    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.middleware("http")
    async def add_request_metadata(request, call_next):
        ACTIVE_REQUESTS.inc()
        try:
            response = await call_next(request)
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code
            ).inc()
            return response
        finally:
            ACTIVE_REQUESTS.dec()

    @application.get("/api/v1/health", tags=["health"])
    async def health_check():
        db_healthy = check_db_connection()
        return {
            "status": "healthy" if db_healthy else "degraded",
            "service": SERVICE_NAME,
            "version": APP_VERSION,
            "timestamp": datetime.utcnow().isoformat(),
            "dependencies": {
                "database": "healthy" if db_healthy else "unhealthy"
            }
        }

    @application.get("/health", tags=["health"])
    async def health_root():
        db_healthy = check_db_connection()
        return {
            "status": "healthy" if db_healthy else "degraded",
            "service": SERVICE_NAME,
            "version": APP_VERSION,
            "timestamp": datetime.utcnow().isoformat(),
            "dependencies": {
                "database": "healthy" if db_healthy else "unhealthy"
            }
        }

    @application.get("/health/ready", tags=["health"])
    async def readiness_probe():
        db_healthy = check_db_connection()
        if not db_healthy:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not ready"
            )
        return {"status": "ready"}

    @application.get("/health/live", tags=["health"])
    async def liveness_probe():
        return {"status": "alive"}

    @application.get("/metrics", tags=["observability"])
    async def metrics():
        return JSONResponse(
            content=generate_latest().decode("utf-8"),
            media_type=CONTENT_TYPE_LATEST
        )

    @application.get("/version", tags=["info"])
    async def version_info():
        return {
            "version": APP_VERSION,
            "service": SERVICE_NAME,
            "environment": os.getenv("ENVIRONMENT", "development"),
            "build_timestamp": datetime.utcnow().isoformat(),
        }

    application.include_router(auth.router, prefix="/api/v1", tags=["auth"])
    application.include_router(returns.router, prefix="/api/v1", tags=["returns"])
    application.include_router(kam.router, prefix="/api/v1", tags=["kam"])
    application.include_router(batch.router, prefix="/api/v1", tags=["batch"])
    application.include_router(kpi.router, prefix="/api/v1", tags=["kpi"])
    application.include_router(reports.router, prefix="/api/v1", tags=["reports"])
    application.include_router(control_tower.router, prefix="/api/v1", tags=["control-tower"])
    application.include_router(admin.router, prefix="/api/v1", tags=["admin"])
    application.include_router(decision.router, prefix="/api/v1", tags=["decision"])
    application.include_router(dropoff.router, prefix="/api/v1", tags=["dropoff"])
    application.include_router(pickup.router, prefix="/api/v1", tags=["pickup"])

    @application.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "code": "INTERNAL_ERROR",
            }
        )

    return application


app = get_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=21001,
        reload=os.getenv("DEBUG", "false").lower() == "true",
        log_level=settings.api.LOG_LEVEL.lower(),
    )
