import logging
import time

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.metrics import HTTP_REQUEST_DURATION_SECONDS, HTTP_REQUESTS_TOTAL
from app.routes import auth, invoices, schools, students

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
)


# Prometheus middleware for request metrics
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    # Skip metrics endpoint itself
    if request.url.path == "/metrics":
        return await call_next(request)

    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    # Record metrics
    HTTP_REQUESTS_TOTAL.labels(
        method=request.method, path=request.url.path, status=response.status_code
    ).inc()

    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=request.method, path=request.url.path
    ).observe(duration)

    return response


# Global exception handlers
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.exception("database_error", extra={"path": request.url.path})
    return JSONResponse(
        status_code=500,
        content={"message": "Unexpected server error"}
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled_exception", extra={"path": request.url.path})
    return JSONResponse(
        status_code=500,
        content={"message": "Unexpected server error"}
    )

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(schools.router, prefix="/api/v1")
app.include_router(students.router, prefix="/api/v1")
app.include_router(invoices.router, prefix="/api/v1")


@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/")
def root():
    return {"message": "School Billing API"}
