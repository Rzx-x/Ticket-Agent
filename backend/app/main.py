import sys
import os
import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(root_dir)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
from app.core.database import create_tables, test_db_connection
from app.core.logging import setup_logging
# Import API routers
from app.api.tickets_simple import router as tickets_router

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create database tables
try:
    create_tables()
except Exception as e:
    logger.error(f"Error creating database tables: {e}")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Smart IT Ticket Management System with AI-powered responses and multi-channel support",
    version=settings.VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    debug=settings.DEBUG
)

# Initialize rate limiter
from app.core.middleware.rate_limiter import setup_rate_limiter, rate_limit_middleware
setup_rate_limiter()

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add middleware
app.middleware("http")(rate_limit_middleware)

# Add request validation middleware
from app.core.middleware.validation import request_validation_middleware
app.middleware("http")(request_validation_middleware)

if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["omnidesk-ai.com", "*.omnidesk-ai.com"]
    )

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Exception handlers
from app.core.exceptions import (
    OmniDeskBaseException,
    create_http_exception,
    ValidationError,
    NotFoundError,
    DatabaseError,
    AIServiceError,
    IntegrationError,
    RateLimitExceeded
)

@app.exception_handler(OmniDeskBaseException)
async def omni_desk_exception_handler(request: Request, exc: OmniDeskBaseException):
    http_exc = create_http_exception(exc)
    logger.error(f"Application error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=http_exc.status_code,
        content={"detail": http_exc.detail}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": {
                "message": "Internal server error",
                "type": exc.__class__.__name__,
                "path": str(request.url)
            }
        }
    )

# Include routers
app.include_router(tickets_router, prefix="/api/v1/tickets", tags=["tickets"])

# Health check endpoints
@app.get("/")
async def root():
    return {
        "message": f"{settings.APP_NAME} is running!",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "healthy"
    }

@app.get("/health")
@app.get("/api/v1/health")
async def health_check():
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "services": {}
    }
    
    # Database check
    try:
        db_status = await test_db_connection()
        health_status["services"]["database"] = "healthy" if db_status else "unhealthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["services"]["database"] = "unhealthy"
    
    # Service checks (will enable when services are available)
    health_status["services"]["ai"] = "not_configured" 
    health_status["services"]["vector_search"] = "not_configured" 
    health_status["services"]["email"] = "not_configured" 
    health_status["services"]["sms"] = "not_configured"
    
    # Overall status
    critical_services = ["database"]
    overall_healthy = all(
        health_status["services"][service] == "healthy" 
        for service in critical_services
    )
    
    if not overall_healthy:
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/api/v1/system/info")
async def system_info():
    """System information endpoint"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "features": {
            "ai_classification": True,
            "vector_search": True,
            "multi_language": True,
            "email_integration": True,
            "sms_integration": True,
            "glpi_integration": True,
            "analytics_dashboard": True
        },
        "supported_sources": ["web", "email", "sms", "glpi", "solman"],
        "supported_languages": ["en", "hi", "hindi+english"]
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Test critical services
    if test_db_connection():
        logger.info("Database connection successful")
    else:
        logger.error("Database connection failed!")
    
    from app.services.ai_service import ai_service
    if ai_service.is_available():
        logger.info("AI service initialized")
    else:
        logger.warning("AI service not available")
    
    from app.services.vector_service import vector_service
    if vector_service.is_available():
        logger.info("Vector search service initialized")
    else:
        logger.warning("Vector search service not available")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {settings.APP_NAME}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )