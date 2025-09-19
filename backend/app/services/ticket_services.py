from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import logging

from db.models import Ticket, TicketResponse, TicketAnalytics, TicketStatus, TicketUrgency
from app.schemas.ticket import TicketCreate, TicketUpdate

logger = logging.getLogger(__name__)

class TicketService:
    def __init__(self):
        self.ticket_counter = 0

    def _to_status(self, value):
        """Convert a string or enum to TicketStatus enum or return None"""
        if value is None:
            return None
        # If already an enum instance
        try:
            if isinstance(value, TicketStatus):
                return value
        except Exception:
            pass
        # Try mapping from string
        try:
            val = str(value).lower()
            for s in TicketStatus:
                if s.value == val or s.name.lower() == val:
                    return s
        except Exception:
            pass
        return None

    def _to_urgency(self, value):
        """Convert a string or enum to TicketUrgency enum or return None"""
        if value is None:
            return None
        try:
            if isinstance(value, TicketUrgency):
                return value
        except Exception:
            pass
        try:
            val = str(value).lower()
            for u in TicketUrgency:
                if u.value == val or u.name.lower() == val:
                    return u
        except Exception:
            pass
        return None
    
    async def create_ticket(self, db: Session, ticket_data: TicketCreate) -> Ticket:
        """Create a new ticket"""
        try:
            # Generate ticket number
            ticket_number = self._generate_ticket_number()
            
            # Create ticket
            ticket = Ticket(
                ticket_number=ticket_number,
                title=ticket_data.title,
                description=ticket_data.description,
                original_text=ticket_data.description,
                source=ticket_data.source,
                source_id=ticket_data.source_id,
                user_email=ticket_data.user_email,
                user_name=ticket_data.user_name,
                user_department=ticket_data.user_department,
                extra_metadata=ticket_data.metadata or {}
            )
            
            db.add(ticket)
            db.commit()
            db.refresh(ticket)
            
            # Create analytics entry
            analytics = TicketAnalytics(ticket_id=ticket.id)
            db.add(analytics)
            db.commit()
            
            logger.info(f"Created ticket: {ticket.ticket_number}")
            return ticket
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating ticket: {e}")
            raise
    
    async def get_tickets(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Ticket]:
        """Get tickets with optional filtering"""
        try:
            query = db.query(Ticket)
            
            # Apply filters
            if status:
                query = query.filter(Ticket.status == status)
            if category:
                query = query.filter(Ticket.category == category)
            
            # Order by creation date (newest first)
            query = query.order_by(Ticket.created_at.desc())
            
            # Apply pagination
            tickets = query.offset(skip).limit(limit).all()
            
            return tickets
            
        except Exception as e:
            logger.error(f"Error fetching tickets: {e}")
            raise
    
    async def get_ticket_by_id(self, db: Session, ticket_id: str) -> Optional[Ticket]:
        """Get ticket by ID"""
        try:
            ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
            return ticket
            
        except Exception as e:
            logger.error(f"Error fetching ticket {ticket_id}: {e}")
            raise
    
    async def update_ticket(
        self, 
        db: Session, 
        ticket_id: str, 
        ticket_update: TicketUpdate
    ) -> Optional[Ticket]:
        """Update ticket"""
        try:
            ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
            if not ticket:
                return None
            
            # Update fields
            update_data = ticket_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(ticket, field, value)
            
            # Update timestamp
            ticket.updated_at = datetime.utcnow()
            
            # Set resolved timestamp if status changed to resolved
            if ticket_update.status == TicketStatus.RESOLVED and not ticket.resolved_at:
                ticket.resolved_at = datetime.utcnow()
                
                # Update analytics
                analytics = db.query(TicketAnalytics).filter(
                    TicketAnalytics.ticket_id == ticket_id
                ).first()
                if analytics:
                    resolution_time = (ticket.resolved_at - ticket.created_at).total_seconds() / 60
                    analytics.resolution_time_minutes = int(resolution_time)
                    analytics.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(ticket)
            
            logger.info(f"Updated ticket: {ticket.ticket_number}")
            return ticket
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating ticket {ticket_id}: {e}")
            raise
    
    async def update_ticket_ai_data(
        self, 
        db: Session, 
        ticket_id: str,
        language_info: Dict[str, Any],
        classification: Dict[str, Any],
        ai_response: Dict[str, Any]
    ) -> bool:
        """Update ticket with AI processing results"""
        try:
            ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
            if not ticket:
                return False
            
            # Update language detection
            ticket.detected_language = language_info.get("primary_language")
            ticket.language_confidence = language_info.get("confidence", 0.0)
            ticket.is_mixed_language = language_info.get("is_mixed", False)
            
            # Update classification (map to enums where appropriate)
            ticket.category = classification.get("category")
            ticket.subcategory = classification.get("subcategory")
            # Map urgency string to enum if possible
            ticket.urgency = self._to_urgency(classification.get("urgency")) or ticket.urgency
            ticket.ai_confidence = classification.get("confidence", 0.0)
            
            # Check if escalation is needed
            if ai_response.get("requires_escalation", False):
                ticket.status = TicketStatus.ESCALATED
            
            ticket.updated_at = datetime.utcnow()
            
            # Create AI response record
            response = TicketResponse(
                ticket_id=ticket_id,
                response_text=ai_response.get("response_text", ""),
                response_language=language_info.get("primary_language"),
                is_ai_response=True,
                is_auto_response=True,
                ai_model_used="claude-3-sonnet",
                confidence_score=ai_response.get("confidence", 0.0)
            )
            
            db.add(response)
            
            # Update analytics
            analytics = db.query(TicketAnalytics).filter(
                TicketAnalytics.ticket_id == ticket_id
            ).first()
            
            if analytics:
                analytics.ai_accuracy_score = classification.get("confidence", 0.0)
                analytics.auto_resolution_attempted = True
                analytics.auto_resolution_successful = not ai_response.get("requires_escalation", False)
                analytics.updated_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"Updated ticket AI data: {ticket.ticket_number}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating ticket AI data {ticket_id}: {e}")
            raise
    
    def _generate_ticket_number(self) -> str:
        """Generate unique ticket number"""
        self.ticket_counter += 1
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        return f"TKT-{timestamp}-{self.ticket_counter:06d}"

# Global instance
ticket_service = TicketService()