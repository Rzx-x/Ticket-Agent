from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TicketSourceEnum(str, Enum):
    EMAIL = "email"
    GLPI = "glpi"
    SOLMAN = "solman"
    SMS = "sms"
    WEB = "web"


class TicketStatusEnum(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class TicketUrgencyEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    source: TicketSourceEnum = TicketSourceEnum.WEB
    source_id: Optional[str] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    user_department: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}


class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TicketStatusEnum] = None
    assigned_to: Optional[str] = None
    urgency: Optional[TicketUrgencyEnum] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None


class TicketResponse(BaseModel):
    id: str
    ticket_number: str
    title: str
    description: str
    source: TicketSourceEnum
    status: TicketStatusEnum
    urgency: Optional[TicketUrgencyEnum]
    category: Optional[str]
    subcategory: Optional[str]
    detected_language: Optional[str]
    is_mixed_language: Optional[bool]
    ai_confidence: Optional[float]
    assigned_to: Optional[str]
    user_email: Optional[str]
    user_name: Optional[str]
    user_department: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TicketResponseCreate(BaseModel):
    ticket_id: str
    response_text: str
    is_ai_response: bool = True
    responder_name: Optional[str] = None
    response_language: Optional[str] = None


class DashboardMetrics(BaseModel):
    total_tickets: int
    open_tickets: int
    resolved_tickets: int
    average_resolution_time: float
    tickets_by_category: Dict[str, int]
    tickets_by_urgency: Dict[str, int]
    ai_success_rate: float
    recent_tickets: List[TicketResponse]
