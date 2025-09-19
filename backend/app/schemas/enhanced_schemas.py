"""
Enhanced API Schemas with Pydantic v2
Provides comprehensive data validation, serialization, and type safety
for all API endpoints with production-ready error handling.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field
from pydantic.networks import EmailStr, HttpUrl
from pydantic.types import UUID4, PositiveInt, constr, conlist
from typing import Optional, List, Dict, Any, Union, Literal
from datetime import datetime, timedelta
from enum import Enum
import re
from decimal import Decimal

# Configuration for all models
class BaseConfig:
    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": []
        }
    )

# Enums for type safety
class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"
    ON_HOLD = "on_hold"

class TicketUrgency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TicketSource(str, Enum):
    WEB = "web"
    EMAIL = "email"
    SMS = "sms"
    GLPI = "glpi"
    SOLMAN = "solman"
    API = "api"
    PHONE = "phone"

class TicketCategory(str, Enum):
    NETWORK = "Network"
    HARDWARE = "Hardware"
    SOFTWARE = "Software"
    EMAIL = "Email"
    ACCOUNT = "Account"
    SECURITY = "Security"
    PRINTER = "Printer"
    TELEPHONY = "Telephony"
    OTHER = "Other"

class UserRole(str, Enum):
    USER = "user"
    AGENT = "agent"
    ADMIN = "admin"
    MANAGER = "manager"

class ResponseType(str, Enum):
    AI_AUTO = "ai_auto"
    AI_ASSISTED = "ai_assisted"
    HUMAN = "human"
    SYSTEM = "system"

# Base schemas
class TimestampMixin(BaseModel):
    """Mixin for timestamp fields"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

class UserInfo(BaseModel, BaseConfig):
    """User information schema"""
    user_id: Optional[str] = Field(None, max_length=50)
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    department: Optional[str] = Field(None, max_length=100)
    role: UserRole = Field(default=UserRole.USER)
    phone: Optional[str] = Field(None, pattern=r'^\+?[\d\s\-\(\)]{7,15}$')
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Name cannot be empty')
        if not re.match(r'^[a-zA-Z\s\-\.]+$', v):
            raise ValueError('Name contains invalid characters')
        return v.strip().title()

class LanguageInfo(BaseModel, BaseConfig):
    """Language detection information"""
    primary_language: str = Field(..., min_length=2, max_length=10)
    confidence: float = Field(..., ge=0.0, le=1.0)
    is_mixed: bool = Field(default=False)
    detected_languages: List[str] = Field(default_factory=list)
    hinglish_score: Optional[float] = Field(None, ge=0.0, le=1.0)

class AIMetadata(BaseModel, BaseConfig):
    """AI processing metadata"""
    model_used: str = Field(..., min_length=1, max_length=100)
    confidence: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: float = Field(..., gt=0)
    gpu_accelerated: bool = Field(default=False)
    language_info: Optional[LanguageInfo] = None
    reasoning: Optional[str] = Field(None, max_length=1000)
    keywords: List[str] = Field(default_factory=list, max_length=20)

# Request schemas
class TicketCreateRequest(BaseModel, BaseConfig):
    """Request schema for creating a new ticket"""
    title: str = Field(
        ..., 
        min_length=5, 
        max_length=500, 
        description="Brief title describing the issue"
    )
    description: str = Field(
        ..., 
        min_length=10, 
        max_length=5000,
        description="Detailed description of the issue"
    )
    source: TicketSource = Field(default=TicketSource.WEB)
    user_info: UserInfo = Field(..., description="Information about the user reporting the issue")
    urgency: Optional[TicketUrgency] = Field(None, description="User-specified urgency (will be validated by AI)")
    category: Optional[TicketCategory] = Field(None, description="User-specified category (will be validated by AI)")
    attachments: List[str] = Field(default_factory=list, max_length=10)
    external_id: Optional[str] = Field(None, max_length=100, description="ID from external system")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context information")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "title": "VPN connection not working from home",
                "description": "Main VPN server se connect nahi ho pa raha office ke servers access karne ke liye. Error message aa raha hai connection timeout.",
                "source": "email",
                "user_info": {
                    "name": "Rajesh Kumar",
                    "email": "rajesh.kumar@powergrid.in",
                    "department": "Finance",
                    "phone": "+91-9876543210"
                },
                "urgency": "high",
                "context": {
                    "user_location": "Mumbai",
                    "device_type": "Windows laptop"
                }
            }]
        }
    )
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        if len(v.strip()) < 10:
            raise ValueError('Description must be at least 10 characters long')
        return v.strip()
    
    @field_validator('attachments')
    @classmethod
    def validate_attachments(cls, v: List[str]) -> List[str]:
        if len(v) > 10:
            raise ValueError('Maximum 10 attachments allowed')
        return v

class TicketUpdateRequest(BaseModel, BaseConfig):
    """Request schema for updating a ticket"""
    title: Optional[str] = Field(None, min_length=5, max_length=500)
    description: Optional[str] = Field(None, min_length=10, max_length=5000)
    status: Optional[TicketStatus] = None
    urgency: Optional[TicketUrgency] = None
    category: Optional[TicketCategory] = None
    assigned_to: Optional[str] = Field(None, max_length=100)
    resolution_notes: Optional[str] = Field(None, max_length=2000)
    internal_notes: Optional[str] = Field(None, max_length=1000)
    updated_by: str = Field(..., max_length=100)
    
class ResponseCreateRequest(BaseModel, BaseConfig):
    """Request schema for creating a ticket response"""
    ticket_id: UUID4 = Field(..., description="ID of the ticket")
    response_text: str = Field(..., min_length=1, max_length=5000)
    response_type: ResponseType = Field(default=ResponseType.HUMAN)
    is_internal: bool = Field(default=False, description="Internal note vs customer-facing response")
    responder_info: UserInfo = Field(..., description="Information about the responder")
    ai_metadata: Optional[AIMetadata] = Field(None, description="AI processing metadata if applicable")
    
class SearchRequest(BaseModel, BaseConfig):
    """Request schema for searching tickets"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    limit: PositiveInt = Field(default=10, le=100)
    offset: int = Field(default=0, ge=0)
    sort_by: str = Field(default="created_at")
    sort_order: Literal["asc", "desc"] = Field(default="desc")
    include_resolved: bool = Field(default=False)
    semantic_search: bool = Field(default=True, description="Use AI-powered semantic search")
    
    @field_validator('filters')
    @classmethod
    def validate_filters(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        allowed_filters = {
            'category', 'status', 'urgency', 'source', 'user_id', 
            'assigned_to', 'date_from', 'date_to', 'department'
        }
        invalid_filters = set(v.keys()) - allowed_filters
        if invalid_filters:
            raise ValueError(f'Invalid filters: {invalid_filters}')
        return v

# Response schemas
class ClassificationResult(BaseModel, BaseConfig):
    """AI classification result"""
    category: TicketCategory = Field(..., description="Predicted category")
    subcategory: str = Field(..., max_length=100)
    urgency: TicketUrgency = Field(..., description="Predicted urgency level")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")
    reasoning: str = Field(..., max_length=1000, description="AI reasoning for classification")
    keywords: List[str] = Field(..., max_length=20, description="Extracted keywords")
    estimated_resolution_time: str = Field(..., max_length=50)
    language_detected: str = Field(..., max_length=10)
    is_mixed_language: bool = Field(...)
    similar_tickets_count: int = Field(default=0, ge=0)

class TicketResponse(BaseModel, BaseConfig):
    """Ticket response schema"""
    id: UUID4 = Field(..., description="Response ID")
    ticket_id: UUID4 = Field(..., description="Associated ticket ID")
    response_text: str = Field(..., description="Response content")
    response_type: ResponseType = Field(..., description="Type of response")
    is_internal: bool = Field(..., description="Internal note flag")
    responder_name: str = Field(..., max_length=100)
    responder_role: UserRole = Field(...)
    ai_metadata: Optional[AIMetadata] = None
    created_at: datetime = Field(..., description="Response timestamp")
    
class TicketDetailResponse(BaseModel, BaseConfig):
    """Comprehensive ticket response schema"""
    id: UUID4 = Field(..., description="Ticket ID")
    ticket_number: str = Field(..., description="Human-readable ticket number")
    title: str = Field(..., description="Ticket title")
    description: str = Field(..., description="Ticket description")
    status: TicketStatus = Field(..., description="Current ticket status")
    urgency: TicketUrgency = Field(..., description="Ticket urgency level")
    category: TicketCategory = Field(..., description="Ticket category")
    subcategory: str = Field(..., description="Ticket subcategory")
    source: TicketSource = Field(..., description="Ticket source")
    
    # User information
    user_info: UserInfo = Field(..., description="Ticket reporter information")
    assigned_to: Optional[str] = Field(None, description="Assigned agent")
    
    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    
    # AI processing
    classification: Optional[ClassificationResult] = None
    language_info: Optional[LanguageInfo] = None
    
    # Responses and notes
    responses: List[TicketResponse] = Field(default_factory=list)
    
    # Metrics
    response_time_minutes: Optional[int] = Field(None, ge=0)
    resolution_time_minutes: Optional[int] = Field(None, ge=0)
    escalation_count: int = Field(default=0, ge=0)
    
    # Additional data
    tags: List[str] = Field(default_factory=list, max_length=20)
    attachments: List[str] = Field(default_factory=list)
    external_id: Optional[str] = None
    
    @computed_field
    @property
    def is_overdue(self) -> bool:
        """Check if ticket is overdue based on urgency and creation time"""
        if self.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
            return False
        
        now = datetime.utcnow()
        hours_since_creation = (now - self.created_at).total_seconds() / 3600
        
        sla_hours = {
            TicketUrgency.CRITICAL: 2,
            TicketUrgency.HIGH: 8,
            TicketUrgency.MEDIUM: 24,
            TicketUrgency.LOW: 72
        }
        
        return hours_since_creation > sla_hours.get(self.urgency, 24)

class PaginatedTicketResponse(BaseModel, BaseConfig):
    """Paginated ticket list response"""
    items: List[TicketDetailResponse] = Field(..., description="List of tickets")
    total: int = Field(..., ge=0, description="Total number of tickets")
    limit: int = Field(..., gt=0, description="Items per page")
    offset: int = Field(..., ge=0, description="Offset from start")
    has_more: bool = Field(..., description="Whether more items are available")
    
    @computed_field
    @property
    def page(self) -> int:
        """Current page number (1-indexed)"""
        return (self.offset // self.limit) + 1
    
    @computed_field
    @property
    def total_pages(self) -> int:
        """Total number of pages"""
        return (self.total + self.limit - 1) // self.limit

class AnalyticsResponse(BaseModel, BaseConfig):
    """Analytics dashboard response"""
    summary: Dict[str, Any] = Field(..., description="Summary statistics")
    ticket_counts_by_status: Dict[TicketStatus, int] = Field(..., description="Tickets by status")
    ticket_counts_by_category: Dict[TicketCategory, int] = Field(..., description="Tickets by category")
    ticket_counts_by_urgency: Dict[TicketUrgency, int] = Field(..., description="Tickets by urgency")
    avg_resolution_time_hours: float = Field(..., ge=0, description="Average resolution time")
    sla_compliance_rate: float = Field(..., ge=0.0, le=1.0, description="SLA compliance rate")
    ai_automation_rate: float = Field(..., ge=0.0, le=1.0, description="AI automation rate")
    top_categories: List[Dict[str, Any]] = Field(..., max_length=10)
    recent_trends: Dict[str, Any] = Field(..., description="Recent trend analysis")
    performance_metrics: Dict[str, float] = Field(..., description="Performance metrics")

class HealthCheckResponse(BaseModel, BaseConfig):
    """Health check response"""
    status: Literal["healthy", "degraded", "unhealthy"] = Field(..., description="Overall health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Deployment environment")
    uptime_seconds: float = Field(..., ge=0)
    services: Dict[str, str] = Field(..., description="Service health statuses")
    
    # Performance metrics
    performance: Dict[str, float] = Field(default_factory=dict)
    
    # AI system status
    ai_status: Dict[str, Any] = Field(default_factory=dict)

# Error response schemas
class ErrorDetail(BaseModel, BaseConfig):
    """Detailed error information"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(None, description="Field that caused the error")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional error context")

class ErrorResponse(BaseModel, BaseConfig):
    """Standard error response"""
    error: bool = Field(default=True)
    message: str = Field(..., description="Main error message")
    details: List[ErrorDetail] = Field(default_factory=list)
    request_id: Optional[str] = Field(None, description="Request tracking ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
class ValidationErrorResponse(ErrorResponse):
    """Validation error response"""
    field_errors: Dict[str, List[str]] = Field(default_factory=dict, description="Field-specific validation errors")

# Success response wrapper
class SuccessResponse(BaseModel, BaseConfig):
    """Generic success response wrapper"""
    success: bool = Field(default=True)
    message: str = Field(default="Operation completed successfully")
    data: Optional[Any] = Field(None, description="Response data")
    request_id: Optional[str] = Field(None, description="Request tracking ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# WebSocket message schemas
class WebSocketMessage(BaseModel, BaseConfig):
    """WebSocket message schema"""
    type: str = Field(..., description="Message type")
    payload: Dict[str, Any] = Field(..., description="Message payload")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    client_id: Optional[str] = Field(None, description="Client identifier")

class TicketUpdateMessage(WebSocketMessage):
    """Real-time ticket update message"""
    type: Literal["ticket_update"] = "ticket_update"
    payload: Dict[str, Any] = Field(..., description="Ticket update data")
    affected_users: List[str] = Field(default_factory=list, description="Users to notify")

# Export all schemas for easy import
__all__ = [
    # Enums
    'TicketStatus', 'TicketUrgency', 'TicketSource', 'TicketCategory', 'UserRole', 'ResponseType',
    
    # Base schemas
    'UserInfo', 'LanguageInfo', 'AIMetadata', 'TimestampMixin',
    
    # Request schemas
    'TicketCreateRequest', 'TicketUpdateRequest', 'ResponseCreateRequest', 'SearchRequest',
    
    # Response schemas
    'ClassificationResult', 'TicketResponse', 'TicketDetailResponse', 
    'PaginatedTicketResponse', 'AnalyticsResponse', 'HealthCheckResponse',
    
    # Error schemas
    'ErrorDetail', 'ErrorResponse', 'ValidationErrorResponse',
    
    # Success schemas
    'SuccessResponse',
    
    # WebSocket schemas
    'WebSocketMessage', 'TicketUpdateMessage'
]