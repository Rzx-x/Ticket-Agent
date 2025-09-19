from fastapi import APIRouter, status, Response
from typing import Dict, Any
from pydantic import BaseModel
from datetime import datetime
import psutil
import asyncio
from loguru import logger

from app.core.database import test_db_connection
from app.services.ai_service import ai_service
from app.services.vector_service import vector_service
from app.integrations.email_service import email_service
from app.integrations.sms_service import sms_service
from app.core.config import settings

router = APIRouter()

class HealthCheck(BaseModel):
    """Health check response model"""
    status: str
    environment: str
    version: str
    timestamp: datetime
    uptime: float
    memory_usage: float
    cpu_usage: float
    services: Dict[str, Dict[str, Any]]

def get_system_health() -> Dict[str, float]:
    """Get system metrics"""
    return {
        "memory_usage": psutil.Process().memory_percent(),
        "cpu_usage": psutil.cpu_percent(interval=0.1)
    }

async def check_service_health() -> Dict[str, Dict[str, Any]]:
    """Check health of all service dependencies"""
    services = {}
    
    # Check database
    try:
        db_ok = await test_db_connection()
        services["database"] = {
            "status": "healthy" if db_ok else "unhealthy",
            "type": "postgresql",
            "url": settings.DATABASE_URL.split("@")[1] if "@" in settings.DATABASE_URL else "localhost"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        services["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check AI service
    try:
        ai_ok = ai_service.is_available()
        services["ai"] = {
            "status": "healthy" if ai_ok else "unhealthy",
            "type": "claude",
            "features": ["classification", "response_generation", "language_detection"]
        }
    except Exception as e:
        logger.error(f"AI service health check failed: {e}")
        services["ai"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check vector service
    try:
        vector_ok = vector_service.is_available()
        collections = vector_service.get_collection_info() if vector_ok else {}
        services["vector_db"] = {
            "status": "healthy" if vector_ok else "unhealthy",
            "type": "qdrant",
            "collections": collections
        }
    except Exception as e:
        logger.error(f"Vector DB health check failed: {e}")
        services["vector_db"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check email service
    try:
        email_ok = email_service.is_configured
        services["email"] = {
            "status": "healthy" if email_ok else "disabled",
            "provider": "smtp"
        }
    except Exception as e:
        logger.error(f"Email service health check failed: {e}")
        services["email"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check SMS service
    try:
        sms_ok = sms_service.is_configured
        services["sms"] = {
            "status": "healthy" if sms_ok else "disabled",
            "provider": "twilio"
        }
    except Exception as e:
        logger.error(f"SMS service health check failed: {e}")
        services["sms"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    return services

@router.get("/health", response_model=HealthCheck)
async def health_check(response: Response):
    """Comprehensive health check endpoint"""
    services = await check_service_health()
    
    # Calculate overall status
    critical_services = ["database", "ai", "vector_db"]
    unhealthy_critical = any(
        services[svc]["status"] == "unhealthy" 
        for svc in critical_services
    )
    
    status = "unhealthy" if unhealthy_critical else "healthy"
    if status == "unhealthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    # Get system metrics
    system_metrics = get_system_health()
    
    return HealthCheck(
        status=status,
        environment=settings.ENVIRONMENT,
        version=settings.VERSION,
        timestamp=datetime.utcnow(),
        uptime=psutil.boot_time(),
        memory_usage=system_metrics["memory_usage"],
        cpu_usage=system_metrics["cpu_usage"],
        services=services
    )

@router.get("/health/live")
async def liveness_check():
    """Basic liveness check - if this fails, the application should be restarted"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow()
    }

@router.get("/health/ready")
async def readiness_check(response: Response):
    """
    Readiness check - if this fails, the application can serve requests
    but might be degraded
    """
    services = await check_service_health()
    
    # Check if critical services are healthy
    critical_services = ["database", "ai", "vector_db"]
    is_ready = all(
        services[svc]["status"] == "healthy" 
        for svc in critical_services
    )
    
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return {
        "status": "ready" if is_ready else "not_ready",
        "timestamp": datetime.utcnow(),
        "services": {
            name: info["status"]
            for name, info in services.items()
            if name in critical_services
        }
    }