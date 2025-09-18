from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Enum, JSON
from sqlalchemy.orm import declarative_base, relationship
import os

# For compatibility across SQLite (dev) and Postgres (prod), use generic types here.
# If you need Postgres-specific types (UUID as native type, JSONB), handle that
# at migration-time or in a separate models file.
SQL_UUID = String(36)
SQL_JSONB = JSON
from datetime import datetime
import uuid
import enum

Base = declarative_base()

class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"

class TicketSource(str, enum.Enum):
    EMAIL = "email"
    GLPI = "glpi"
    SOLMAN = "solman"
    SMS = "sms"
    WEB = "web"

class TicketUrgency(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(SQL_UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_number = Column(String(50), unique=True, nullable=False)
    
    # Source information
    source = Column(Enum(TicketSource), nullable=False)
    source_id = Column(String(100))  # External system ID
    
    # Content
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    original_text = Column(Text, nullable=False)  # Raw input
    
    # Language detection
    detected_language = Column(String(50))
    language_confidence = Column(Float)
    is_mixed_language = Column(Boolean, default=False)
    
    # AI Classification
    category = Column(String(100))
    subcategory = Column(String(100))
    urgency = Column(Enum(TicketUrgency), default=TicketUrgency.MEDIUM)
    ai_confidence = Column(Float)
    
    # Status tracking
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN)
    assigned_to = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    # User information
    user_email = Column(String(255))
    user_name = Column(String(255))
    user_department = Column(String(100))
    
    # Additional metadata (use a different attribute name to avoid conflict with SQLAlchemy's metadata)
    extra_metadata = Column(SQL_JSONB, name='metadata')  # Flexible field for extra data
    
    # Relationships
    responses = relationship("TicketResponse", back_populates="ticket")
    analytics = relationship("TicketAnalytics", back_populates="ticket", uselist=False)

class TicketResponse(Base):
    __tablename__ = "ticket_responses"
    
    id = Column(SQL_UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(SQL_UUID, ForeignKey("tickets.id"), nullable=False)
    
    # Response content
    response_text = Column(Text, nullable=False)
    response_language = Column(String(50))
    
    # Response type
    is_ai_response = Column(Boolean, default=True)
    is_auto_response = Column(Boolean, default=False)
    responder_name = Column(String(255))
    
    # AI metadata
    ai_model_used = Column(String(100))
    confidence_score = Column(Float)
    response_time_ms = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    ticket = relationship("Ticket", back_populates="responses")

class TicketAnalytics(Base):
    __tablename__ = "ticket_analytics"
    
    id = Column(SQL_UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(SQL_UUID, ForeignKey("tickets.id"), nullable=False)
    
    # Performance metrics
    first_response_time_minutes = Column(Integer)
    resolution_time_minutes = Column(Integer)
    escalation_count = Column(Integer, default=0)
    
    # AI metrics
    ai_accuracy_score = Column(Float)
    similar_tickets_found = Column(Integer, default=0)
    auto_resolution_attempted = Column(Boolean, default=False)
    auto_resolution_successful = Column(Boolean, default=False)
    
    # User satisfaction (if collected)
    user_satisfaction_score = Column(Integer)  # 1-5
    user_feedback = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ticket = relationship("Ticket", back_populates="analytics")

class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"
    
    id = Column(SQL_UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Content
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)
    
    # Classification
    category = Column(String(100), nullable=False)
    subcategory = Column(String(100))
    tags = Column(SQL_JSONB)  # Array of tags
    
    # Language
    language = Column(String(50), default="english")
    
    # Usage metrics
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)