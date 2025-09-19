from typing import Any, Dict, Optional
from fastapi import HTTPException, status

class OmniDeskBaseException(Exception):
    """Base exception for OmniDesk application"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class DatabaseError(OmniDeskBaseException):
    """Database related errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.details = details
        super().__init__(message)

class ValidationError(OmniDeskBaseException):
    """Data validation errors"""
    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message)

class AIServiceError(OmniDeskBaseException):
    """AI service related errors"""
    def __init__(self, message: str, service: Optional[str] = None):
        self.service = service
        super().__init__(message)

class IntegrationError(OmniDeskBaseException):
    """Third-party integration errors"""
    def __init__(self, message: str, integration: str):
        self.integration = integration
        super().__init__(message)

class RateLimitExceeded(OmniDeskBaseException):
    """Rate limit exceeded error"""
    pass

class NotFoundError(OmniDeskBaseException):
    """Resource not found error"""
    def __init__(self, resource_type: str, resource_id: str):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(f"{resource_type} with id {resource_id} not found")

def create_http_exception(exc: Exception) -> HTTPException:
    """Convert application exceptions to HTTPException"""
    if isinstance(exc, ValidationError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": str(exc),
                "field": exc.field
            }
        )
    elif isinstance(exc, NotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": str(exc),
                "resource_type": exc.resource_type,
                "resource_id": exc.resource_id
            }
        )
    elif isinstance(exc, RateLimitExceeded):
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"message": str(exc)}
        )
    elif isinstance(exc, AIServiceError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "message": str(exc),
                "service": exc.service
            }
        )
    elif isinstance(exc, IntegrationError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "message": str(exc),
                "integration": exc.integration
            }
        )
    elif isinstance(exc, DatabaseError):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": str(exc),
                "details": exc.details
            }
        )
    else:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": str(exc)}
        )