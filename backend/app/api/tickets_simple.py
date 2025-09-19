from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid
import logging

from app.core.database import get_db
from db.models import Ticket, TicketResponse, TicketAnalytics, TicketSource, TicketStatus, TicketUrgency
from pydantic import BaseModel, EmailStr

logger = logging.getLogger(__name__)

router = APIRouter()

# Request/Response Models
class TicketCreateRequest(BaseModel):
    title: str
    description: str
    reporter_email: EmailStr
    reporter_name: str
    category: str
    priority: str = "medium"
    department: Optional[str] = None
    tags: Optional[List[str]] = []

class TicketUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    department: Optional[str] = None

class TicketResponseModel(BaseModel):
    id: str
    title: str
    description: str
    reporter_email: str
    reporter_name: str
    category: str
    priority: str
    status: str
    department: Optional[str]
    ai_classification: Optional[dict] = None
    ai_suggestions: List[str] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TicketListResponse(BaseModel):
    tickets: List[TicketResponseModel]
    total: int
    page: int
    per_page: int
    pages: int

# Helper functions
def create_ticket_response_model(ticket: Ticket) -> TicketResponseModel:
    """Convert database ticket to response model"""
    return TicketResponseModel(
        id=ticket.id,
        title=ticket.title,
        description=ticket.description,
        reporter_email=ticket.user_email or "",
        reporter_name=ticket.user_name or "",
        category=ticket.category or "General",
        priority=ticket.urgency.value if ticket.urgency else "medium",
        status=ticket.status.value if ticket.status else "open",
        department=ticket.user_department or "",
        ai_classification={
            "confidence": ticket.ai_confidence or 0.0,
            "category": ticket.category,
            "subcategory": ticket.subcategory
        },
        ai_suggestions=[],  # Can be populated from AI service
        created_at=ticket.created_at,
        updated_at=ticket.updated_at
    )

# API Endpoints
@router.post("", response_model=TicketResponseModel, status_code=status.HTTP_201_CREATED)
async def create_ticket(ticket_data: TicketCreateRequest, db: Session = Depends(get_db)):
    """Create a new ticket"""
    try:
        logger.info(f"Creating ticket: {ticket_data.title}")
        
        # Generate ticket number
        ticket_number = f"TKT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Map priority to urgency enum
        urgency_map = {
            "low": TicketUrgency.LOW,
            "medium": TicketUrgency.MEDIUM,
            "high": TicketUrgency.HIGH,
            "critical": TicketUrgency.CRITICAL
        }
        urgency = urgency_map.get(ticket_data.priority.lower(), TicketUrgency.MEDIUM)
        
        # Create new ticket
        new_ticket = Ticket(
            id=str(uuid.uuid4()),
            ticket_number=ticket_number,
            title=ticket_data.title,
            description=ticket_data.description,
            original_text=ticket_data.description,
            user_email=ticket_data.reporter_email,
            user_name=ticket_data.reporter_name,
            user_department=ticket_data.department,
            category=ticket_data.category,
            urgency=urgency,
            status=TicketStatus.OPEN,
            source=TicketSource.WEB
        )
        
        db.add(new_ticket)
        db.commit()
        db.refresh(new_ticket)
        
        logger.info(f"Ticket created successfully: {new_ticket.id}")
        return create_ticket_response_model(new_ticket)
        
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create ticket: {str(e)}"
        )

@router.get("", response_model=TicketListResponse)
async def list_tickets(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None), 
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List tickets with filtering and pagination"""
    try:
        logger.info(f"Listing tickets - page: {page}, per_page: {per_page}")
        
        # Build query
        query = db.query(Ticket)
        
        # Apply filters
        if status:
            try:
                status_enum = TicketStatus(status.lower())
                query = query.filter(Ticket.status == status_enum)
            except ValueError:
                pass  # Invalid status, ignore filter
                
        if priority:
            try:
                urgency_enum = TicketUrgency(priority.lower())
                query = query.filter(Ticket.urgency == urgency_enum)
            except ValueError:
                pass  # Invalid priority, ignore filter
                
        if category:
            query = query.filter(Ticket.category == category)
            
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Ticket.title.ilike(search_pattern)) |
                (Ticket.description.ilike(search_pattern)) |
                (Ticket.user_name.ilike(search_pattern))
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering (newest first)
        offset = (page - 1) * per_page
        tickets = query.order_by(Ticket.created_at.desc()).offset(offset).limit(per_page).all()
        
        # Calculate pagination info
        pages = (total + per_page - 1) // per_page
        
        # Convert to response models
        ticket_responses = [create_ticket_response_model(ticket) for ticket in tickets]
        
        return TicketListResponse(
            tickets=ticket_responses,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Error listing tickets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tickets: {str(e)}"
        )

@router.get("/{ticket_id}", response_model=TicketResponseModel)
async def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    """Get a specific ticket by ID"""
    try:
        logger.info(f"Getting ticket: {ticket_id}")
        
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket {ticket_id} not found"
            )
        
        return create_ticket_response_model(ticket)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ticket {ticket_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ticket: {str(e)}"
        )

@router.patch("/{ticket_id}", response_model=TicketResponseModel)
async def update_ticket(
    ticket_id: str, 
    ticket_update: TicketUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update a specific ticket"""
    try:
        logger.info(f"Updating ticket: {ticket_id}")
        
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket {ticket_id} not found"
            )
        
        # Update fields that were provided
        update_data = ticket_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == "priority" and value:
                # Map priority to urgency enum
                urgency_map = {
                    "low": TicketUrgency.LOW,
                    "medium": TicketUrgency.MEDIUM,
                    "high": TicketUrgency.HIGH,
                    "critical": TicketUrgency.CRITICAL
                }
                if value.lower() in urgency_map:
                    ticket.urgency = urgency_map[value.lower()]
            elif field == "status" and value:
                # Map status to status enum
                try:
                    status_enum = TicketStatus(value.lower())
                    ticket.status = status_enum
                except ValueError:
                    pass  # Invalid status, ignore
            elif hasattr(ticket, field):
                setattr(ticket, field, value)
        
        ticket.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(ticket)
        
        logger.info(f"Ticket updated successfully: {ticket_id}")
        return create_ticket_response_model(ticket)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ticket {ticket_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update ticket: {str(e)}"
        )

@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket(ticket_id: str, db: Session = Depends(get_db)):
    """Delete a specific ticket"""
    try:
        logger.info(f"Deleting ticket: {ticket_id}")
        
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket {ticket_id} not found"
            )
        
        db.delete(ticket)
        db.commit()
        
        logger.info(f"Ticket deleted successfully: {ticket_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting ticket {ticket_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete ticket: {str(e)}"
        )