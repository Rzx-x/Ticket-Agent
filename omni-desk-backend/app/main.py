from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import logging

from app.core.config import settings
from app.core.database import Base, engine, test_db_connection
from app.core.logging import setup_logging
from app.api.tickets import router as tickets_router

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create database tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
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

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

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

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "path": str(request.url)}
    )

# Include routers
app.include_router(
    tickets_router, 
    prefix="/api/v1/tickets", 
    tags=["tickets"]
)

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
    health_status["services"]["database"] = "healthy" if test_db_connection() else "unhealthy"
    
    # AI service check
    from app.services.ai_service import ai_service
    health_status["services"]["ai"] = "healthy" if ai_service.is_available() else "unavailable"
    
    # Vector service check
    from app.services.vector_service import vector_service
    health_status["services"]["vector_search"] = "healthy" if vector_service.is_available() else "unavailable"
    
    # Email service check
    from app.integrations.email_service import email_service
    health_status["services"]["email"] = "configured" if email_service.is_configured else "not_configured"
    
    # SMS service check
    from app.integrations.sms_service import sms_service
    health_status["services"]["sms"] = "configured" if sms_service.is_configured else "not_configured"
    
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