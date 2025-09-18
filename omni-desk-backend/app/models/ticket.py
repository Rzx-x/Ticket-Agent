from sqlalchemy import Column, String, DateTime, Text, Float, Boolean, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from app.core.database import Base

class Ticket(Base):
    __tablename__ = "tickets"
    
    # Primary fields
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_number = Column(String, unique=True, index=True, nullable=False)
    external_id = Column(String, nullable=True, index=True)  # For GLPI/Solman integration
    
    # Source and user info
    source = Column(String, nullable=False, index=True)  # email, sms, glpi, solman, web
    user_email = Column(String, nullable=False, index=True)
    user_phone = Column(String, nullable=True)
    user_name = Column(String, nullable=True)
    
    # Ticket content
    subject = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    language = Column(String, default="en")
    
    # Classification
    category = Column(String, nullable=True, index=True)
    subcategory = Column(String, nullable=True)
    urgency = Column(String, default="medium", index=True)
    priority = Column(Integer, default=2)  # 1=low, 2=medium, 3=high, 4=critical
    status = Column(String, default="open", index=True)
    
    # Assignment
    assigned_to = Column(String, nullable=True, index=True)
    assigned_group = Column(String, nullable=True)
    
    # AI Processing
    ai_processed = Column(Boolean, default=False)
    ai_response = Column(Text, nullable=True)
    ai_confidence = Column(Float, default=0.0)
    ai_suggestions = Column(Text, nullable=True)  # JSON string
    
    # Resolution
    resolution_notes = Column(Text, nullable=True)
    resolution_time_minutes = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    
    # Metadata
    metadata = Column(Text, nullable=True)  # JSON string for additional data
    tags = Column(String, nullable=True)  # Comma-separated tags
    
    # Relationships
    interactions = relationship("TicketInteraction", back_populates="ticket", cascade="all, delete-orphan")
    attachments = relationship("TicketAttachment", back_populates="ticket", cascade="all, delete-orphan")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_ticket_status_created', 'status', 'created_at'),
        Index('idx_ticket_category_urgency', 'category', 'urgency'),
        Index('idx_ticket_user_email_created', 'user_email', 'created_at'),
    )

class TicketInteraction(Base):
    __tablename__ = "ticket_interactions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(String, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Interaction details
    interaction_type = Column(String, nullable=False)  # user_message, ai_response, agent_response, system_note, email_sent
    content = Column(Text, nullable=False)
    sender = Column(String, nullable=True)
    recipient = Column(String, nullable=True)
    
    # Metadata
    is_internal = Column(Boolean, default=False)  # Internal notes vs customer communication
    metadata = Column(Text, nullable=True)  # JSON for additional data
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationship
    ticket = relationship("Ticket", back_populates="interactions")

class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(String, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    
    # File details
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String, nullable=False)
    
    # Metadata
    uploaded_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    ticket = relationship("Ticket", back_populates="attachments")

class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    
    # Classification
    category = Column(String, nullable=False, index=True)
    tags = Column(String, nullable=True)  # Comma-separated
    language = Column(String, default="en")
    
    # Status
    is_published = Column(Boolean, default=True)
    view_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)
    
    # Metadata
    author = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)