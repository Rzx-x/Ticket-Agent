from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Enums
class TicketSource(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    GLPI = "glpi"
    SOLMAN = "solman"
    WEB = "web"
    PHONE = "phone"

class TicketUrgency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"

class InteractionType(str, Enum):
    USER_MESSAGE = "user_message"
    AI_RESPONSE = "ai_response"
    AGENT_RESPONSE = "agent_response"
    SYSTEM_NOTE = "system_note"
    EMAIL_SENT = "email_sent"
    SMS_SENT = "sms_sent"

# Request Schemas
class TicketCreate(BaseModel):
    source: TicketSource = TicketSource.WEB
    user_email: str = Field(..., min_length=5, max_length=254)
    user_phone: Optional[str] = Field(None, max_length=20)
    user_name: Optional[str] = Field(None, max_length=100)
    subject: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    urgency: TicketUrgency = TicketUrgency.MEDIUM
    category: Optional[str] = None
    external_id: Optional[str] = None  # For external system integration

class TicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    assigned_to: Optional[str] = None
    assigned_group: Optional[str] = None
    resolution_notes: Optional[str] = None
    category: Optional[str] = None
    urgency: Optional[TicketUrgency] = None
    tags: Optional[str] = None

class InteractionCreate(BaseModel):
    interaction_type: InteractionType
    content: str = Field(..., min_length=1, max_length=5000)
    sender: Optional[str] = None
    recipient: Optional[str] = None
    is_internal: bool = False

# Response Schemas
class TicketInteractionResponse(BaseModel):
    id: str
    ticket_id: str
    interaction_type: str
    content: str
    sender: Optional[str]
    recipient: Optional[str]
    is_internal: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class TicketAttachmentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    uploaded_by: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class TicketResponse(BaseModel):
    id: str
    ticket_number: str
    external_id: Optional[str]
    source: str
    user_email: str
    user_phone: Optional[str]
    user_name: Optional[str]
    subject: str
    description: str
    language: str
    category: Optional[str]
    subcategory: Optional[str]
    urgency: str
    priority: int
    status: str
    assigned_to: Optional[str]
    assigned_group: Optional[str]
    ai_processed: bool
    ai_response: Optional[str]
    ai_confidence: float
    resolution_notes: Optional[str]
    resolution_time_minutes: Optional[int]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    tags: Optional[str]
    interactions: List[TicketInteractionResponse] = []
    attachments: List[TicketAttachmentResponse] = []
    
    class Config:
        from_attributes = True

class TicketSummary(BaseModel):
    id: str
    ticket_number: str
    subject: str
    status: str
    urgency: str
    category: Optional[str]
    created_at: datetime
    user_email: str
    ai_processed: bool

# Analytics Schemas
class AnalyticsResponse(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    closed_tickets: int
    average_resolution_time_hours: float
    tickets_by_category: Dict[str, int]
    tickets_by_urgency: Dict[str, int]
    tickets_by_source: Dict[str, int]
    ai_processing_rate: float
    recent_activity: List[Dict[str, Any]]

# Search Schemas
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    limit: int = Field(5, ge=1, le=20)
    category_filter: Optional[str] = None
    status_filter: Optional[TicketStatus] = None
    urgency_filter: Optional[TicketUrgency] = None

class SimilarTicketResponse(BaseModel):
    ticket_id: str
    ticket_number: str
    subject: str
    category: Optional[str]
    similarity_score: float
    status: str
    resolution_notes: Optional[str]