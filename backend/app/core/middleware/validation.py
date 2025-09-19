from fastapi import Request
from app.core.exceptions import ValidationError
import json
from typing import Callable, Dict, Any
import re

class RequestValidator:
    """Request validation middleware"""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format"""
        # Basic international phone format validation
        pattern = r'^\+?[1-9]\d{1,14}$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def validate_length(text: str, min_length: int, max_length: int) -> bool:
        """Validate text length"""
        text_len = len(text.strip())
        return min_length <= text_len <= max_length
    
    @staticmethod
    def sanitize_string(text: str) -> str:
        """Basic string sanitization"""
        # Remove null bytes and other control characters
        text = ''.join(char for char in text if ord(char) >= 32)
        return text.strip()

    @staticmethod
    async def validate_json_body(body: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize JSON request body"""
        sanitized = {}
        
        for key, value in body.items():
            if isinstance(value, str):
                sanitized[key] = RequestValidator.sanitize_string(value)
            elif isinstance(value, (int, float, bool, list, dict)):
                sanitized[key] = value
            elif value is None:
                sanitized[key] = None
            else:
                raise ValidationError(f"Invalid type for field {key}")
                
        return sanitized

async def request_validation_middleware(request: Request, call_next: Callable):
    """Middleware for request validation"""
    
    # Skip validation for non-API routes
    if not request.url.path.startswith("/api/"):
        return await call_next(request)
    
    # Validate Content-Type for POST/PUT/PATCH requests
    if request.method in ["POST", "PUT", "PATCH"]:
        content_type = request.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            raise ValidationError(
                "Content-Type must be application/json",
                field="content-type"
            )
        
        # Read and validate request body
        try:
            body = await request.json()
        except json.JSONDecodeError:
            raise ValidationError("Invalid JSON body")
        
        # Validate and sanitize body
        validated_body = await RequestValidator.validate_json_body(body)
        
        # Update request with validated body
        # Note: Since FastAPI's Request is immutable, we'll need to handle
        # the validated body in the route handlers
        setattr(request.state, "validated_body", validated_body)
    
    response = await call_next(request)
    return response