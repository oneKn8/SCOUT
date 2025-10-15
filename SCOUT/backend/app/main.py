"""
SCOUT Backend - FastAPI Application
Local-first resume management system
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import time
import uuid

from app.core.config import settings
from app.core.logging import setup_logging
from app.api import uploads, parsing, metrics, encryption

# Setup structured logging
setup_logging()
logger = structlog.get_logger()

app = FastAPI(
    title="SCOUT Backend",
    description="Local-first resume and profile management system",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all requests with structured logging and PII redaction"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    # Add request ID to request state for use in endpoints
    request.state.request_id = request_id

    # Log request start
    logger.info(
        "Request started",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        query_params=dict(request.query_params),
        user_agent=request.headers.get("user-agent", ""),
    )

    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time

    # Log request completion
    logger.info(
        "Request completed",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time=round(process_time, 4),
    )

    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "scout-backend", "version": "0.1.0"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "SCOUT Backend API", "version": "0.1.0"}


# Include API routers
app.include_router(uploads.router, prefix="/api/uploads", tags=["uploads"])
app.include_router(parsing.router, prefix="/api/parsing", tags=["parsing"])
app.include_router(metrics.router, tags=["metrics"])
app.include_router(encryption.router, tags=["encryption"])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with structured logging"""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    logger.error(
        "Unhandled exception",
        request_id=request_id,
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        path=request.url.path,
        method=request.method,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "request_id": request_id,
            "message": "An unexpected error occurred. Please try again.",
        },
    )