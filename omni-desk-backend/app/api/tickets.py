from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, and_, or_
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import os
import aiofiles

from app.core.database import get_db
from app.models.ticket import Ticket, TicketInteraction, TicketAttachment
from app.schemas.ticket import *
from app.services.ai_service import ai_service
from app.services.vector_service import vector_service
from app.integrations.email_service import email_service
from app.integrations.sms_service import sms_service

import logging
logger = logging.getLogger(__name__)

router = APIRouter()

def generate_ticket_number() -> str:
    """Generate unique ticket number"""
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M')
    unique_id = str(uuid.uuid4())[:6].upper()
    return f"TKT-{timestamp}-{unique_id}"

async def process_ticket_with_ai(ticket_id: str):
    """Background task to process ticket with AI"""
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            logger.warning(f"Ticket {ticket_id} not found for AI processing")
            return
        
        logger.info(f"Processing ticket {ticket_id} with AI")
        
        # AI classification
        classification = await ai_service.classify_ticket(ticket.subject, ticket.description)
        
        # Update ticket with AI insights
        ticket.category = classification.get("category", "Other")
        ticket.subcategory = classification.get("subcategory")
        ticket.ai_confidence = classification.get("confidence", 0.0)
        ticket.ai_processed = True
        
        # Update urgency if AI suggests higher priority
        ai_urgency = classification.get("urgency", "medium")
        urgency_priority = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        current_priority = urgency_priority.get(ticket.urgency, 2)
        ai_priority = urgency_priority.get(ai_urgency, 2)
        
        if ai_priority > current_priority:
            ticket.urgency = ai_urgency
            ticket.priority = ai_priority
        
        # Generate AI response
        ai_response = await ai_service.generate_response(
            ticket.subject, 
            ticket.description, 
            ticket.language, 
            ticket.category,
            ticket.user_name
        )
        ticket.ai_response = ai_response
        
        # Create AI interaction record
        ai_interaction = TicketInteraction(
            ticket_id=ticket_id,
            interaction_type="ai_response",
            content=ai_response,
            sender="AI Assistant"
        )
        
        db.add(ai_interaction)
        
        # Add to vector database for similarity search
        if vector_service.is_available():
            content = f"{ticket.subject} {ticket.description}"
            metadata = {
                "ticket_number": ticket.ticket_number,
                "category": ticket.category,
                "urgency": ticket.urgency,
                "status": ticket.status,
                "language": ticket.language
            }
            await vector_service.add_ticket_vector(ticket_id, content, metadata)
        
        db.commit()
        
        # Send response via appropriate channel
        if ticket.source == "email" and email_service.is_configured:
            await email_service.send_ticket_response(
                ticket.user_email,
                ticket.ticket_number,
                ticket.subject,
                ai_response
            )
        elif ticket.source == "sms" and sms_service.is_configured and ticket.user_phone:
            await sms_service.send_ticket_response(
                ticket.user_phone,
                ticket.ticket_number,
                ai_response
            )
        
        logger.info(f"Successfully processed ticket {ticket_id}: {ticket.category} - {ticket.urgency}")
        
    except Exception as e:
        logger.error(f"Error processing ticket {ticket_id} with AI: {e}")
        db.rollback()
    finally:
        db.close()

@router.post("/", response_model=TicketResponse)
async def create_ticket(
    ticket: TicketCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new support ticket"""
    try:
        # Generate unique ticket number
        ticket_number = generate_ticket_number()
        
        # Detect language
        language = ai_service.detect_language(f"{ticket.subject} {ticket.description}")
        
        # Create ticket in database
        db_ticket = Ticket(
            id=str(uuid.uuid4()),
            ticket_number=ticket_number,
            external_id=ticket.external_id,
            source=ticket.source.value,
            user_email=ticket.user_email.lower().strip(),
            user_phone=ticket.user_phone,
            user_name=ticket.user_name,
            subject=ticket.subject.strip(),
            description=ticket.description.strip(),
            language=language,
            urgency=ticket.urgency.value,
            priority={"low": 1, "medium": 2, "high": 3, "critical": 4}.get(ticket.urgency.value, 2),
            category=ticket.category
        )
        
        # Create initial interaction
        initial_interaction = TicketInteraction(
            ticket_id=db_ticket.id,
            interaction_type="user_message",
            content=f"Subject: {ticket.subject}\n\nDescription: {ticket.description}",
            sender=ticket.user_email
        )
        
        db.add(db_ticket)
        db.add(initial_interaction)
        db.commit()
        db.refresh(db_ticket)
        
        logger.info(f"Created ticket {ticket_number} from {ticket.source.value}")
        
        # Process ticket with AI in background
        if ai_service.is_available():
            background_tasks.add_task(process_ticket_with_ai, db_ticket.id)
        
        # Reload ticket with interactions
        db_ticket = db.query(Ticket).options(
            joinedload(Ticket.interactions),
            joinedload(Ticket.attachments)
        ).filter(Ticket.id == db_ticket.id).first()
        
        return db_ticket
        
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create ticket: {str(e)}")

@router.get("/", response_model=List[TicketSummary])
async def get_tickets(
    skip: int = Query(0, ge=0, description="Number of tickets to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of tickets to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    urgency: Optional[str] = Query(None, description="Filter by urgency"),
    user_email: Optional[str] = Query(None, description="Filter by user email"),
    search: Optional[str] = Query(None, description="Search in subject/description"),
    db: Session = Depends(get_db)
):
    """Get tickets with filtering and pagination"""
    try:
        query = db.query(Ticket)
        
        # Apply filters
        if status:
            query = query.filter(Ticket.status == status)
        if category:
            query = query.filter(Ticket.category == category)
        if urgency:
            query = query.filter(Ticket.urgency == urgency)
        if user_email:
            query = query.filter(Ticket.user_email.ilike(f"%{user_email}%"))
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Ticket.subject.ilike(search_term),
                    Ticket.description.ilike(search_term),
                    Ticket.ticket_number.ilike(search_term)
                )
            )
        
        # Order by priority and creation date
        query = query.order_by(desc(Ticket.priority), desc(Ticket.created_at))
        
        # Apply pagination
        tickets = query.offset(skip).limit(limit).all()
        
        logger.info(f"Retrieved {len(tickets)} tickets with filters")
        return tickets
        
    except Exception as e:
        logger.error(f"Error retrieving tickets: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tickets")

@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    """Get a specific ticket with all interactions"""
    try:
        ticket = db.query(Ticket).options(
            joinedload(Ticket.interactions),
            joinedload(Ticket.attachments)
        ).filter(Ticket.id == ticket_id).first()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        logger.info(f"Retrieved ticket {ticket.ticket_number}")
        return ticket
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving ticket {ticket_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve ticket")

@router.put("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: str,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db)
):
    """Update ticket details"""
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Update fields
        update_data = ticket_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(ticket, field) and value is not None:
                if field == "urgency":
                    ticket.urgency = value.value if hasattr(value, 'value') else value
                    ticket.priority = {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(ticket.urgency, 2)
                elif field == "status":
                    ticket.status = value.value if hasattr(value, 'value') else value
                    if ticket.status in ["resolved", "closed"]:
                        ticket.resolved_at = datetime.utcnow()
                    if ticket.status == "closed":
                        ticket.closed_at = datetime.utcnow()
                else:
                    setattr(ticket, field, value)
        
        ticket.updated_at = datetime.utcnow()
        
        # Create system note for the update
        system_note = TicketInteraction(
            ticket_id=ticket_id,
            interaction_type="system_note",
            content=f"Ticket updated: {', '.join([f'{k}={v}' for k, v in update_data.items()])}",
            sender="System",
            is_internal=True
        )
        
        db.add(system_note)
        db.commit()
        db.refresh(ticket)
        
        logger.info(f"Updated ticket {ticket.ticket_number}")
        return ticket
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ticket {ticket_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update ticket")

@router.post("/{ticket_id}/interactions", response_model=TicketInteractionResponse)
async def add_interaction(
    ticket_id: str,
    interaction: InteractionCreate,
    db: Session = Depends(get_db)
):
    """Add an interaction to a ticket"""
    try:
        # Verify ticket exists
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Create interaction
        db_interaction = TicketInteraction(
            ticket_id=ticket_id,
            interaction_type=interaction.interaction_type.value,
            content=interaction.content,
            sender=interaction.sender,
            recipient=interaction.recipient,
            is_internal=interaction.is_internal
        )
        
        db.add(db_interaction)
        
        # Update ticket timestamp
        ticket.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_interaction)
        
        logger.info(f"Added interaction to ticket {ticket.ticket_number}")
        return db_interaction
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding interaction to ticket {ticket_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to add interaction")

@router.post("/{ticket_id}/regenerate-ai-response")
async def regenerate_ai_response(
    ticket_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Regenerate AI response for a ticket"""
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        if not ai_service.is_available():
            raise HTTPException(status_code=503, detail="AI service unavailable")
        
        # Generate new AI response
        ai_response = await ai_service.generate_response(
            ticket.subject, 
            ticket.description, 
            ticket.language, 
            ticket.category or "Other",
            ticket.user_name
        )
        
        ticket.ai_response = ai_response
        ticket.updated_at = datetime.utcnow()
        
        # Create new AI interaction
        ai_interaction = TicketInteraction(
            ticket_id=ticket_id,
            interaction_type="ai_response",
            content=ai_response,
            sender="AI Assistant (Regenerated)"
        )
        
        db.add(ai_interaction)
        db.commit()
        
        logger.info(f"Regenerated AI response for ticket {ticket.ticket_number}")
        return {"message": "AI response regenerated successfully", "response": ai_response}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating AI response for ticket {ticket_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to regenerate AI response")

@router.get("/{ticket_id}/similar")
async def get_similar_tickets(
    ticket_id: str,
    limit: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db)
):
    """Find similar tickets using vector search"""
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        if not vector_service.is_available():
            return {"similar_tickets": [], "message": "Vector search service unavailable"}
        
        query_text = f"{ticket.subject} {ticket.description}"
        similar_tickets = await vector_service.search_similar_tickets(
            query_text, 
            limit=limit, 
            exclude_ticket_id=ticket_id,
            category_filter=ticket.category
        )
        
        # Get ticket details for similar tickets
        result_tickets = []
        for similar in similar_tickets:
            similar_ticket = db.query(Ticket).filter(
                Ticket.id == similar["ticket_id"]
            ).first()
            
            if similar_ticket:
                result_tickets.append({
                    "ticket_id": similar_ticket.id,
                    "ticket_number": similar_ticket.ticket_number,
                    "subject": similar_ticket.subject,
                    "category": similar_ticket.category,
                    "status": similar_ticket.status,
                    "similarity_score": similar["similarity_score"],
                    "resolution_notes": similar_ticket.resolution_notes
                })
        
        logger.info(f"Found {len(result_tickets)} similar tickets for {ticket.ticket_number}")
        return {"similar_tickets": result_tickets}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding similar tickets for {ticket_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to find similar tickets")

@router.post("/{ticket_id}/upload")
async def upload_attachment(
    ticket_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload attachment to ticket"""
    try:
        # Verify ticket exists
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Validate file
        if file.size > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=413, detail="File too large")
        
        # Create uploads directory if it doesn't exist
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = file.filename.split(".")[-1] if "." in file.filename else ""
        unique_filename = f"{ticket_id}_{uuid.uuid4().hex[:8]}.{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Create attachment record
        attachment = TicketAttachment(
            ticket_id=ticket_id,
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=len(content),
            content_type=file.content_type,
            uploaded_by=ticket.user_email
        )
        
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
        
        logger.info(f"Uploaded attachment {file.filename} to ticket {ticket.ticket_number}")
        return {
            "message": "File uploaded successfully",
            "attachment_id": attachment.id,
            "filename": attachment.original_filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading attachment to ticket {ticket_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to upload attachment")

# Analytics endpoint
@router.get("/analytics/dashboard", response_model=AnalyticsResponse)
async def get_analytics(db: Session = Depends(get_db)):
    """Get comprehensive ticket analytics"""
    try:
        # Basic counts
        total_tickets = db.query(Ticket).count()
        open_tickets = db.query(Ticket).filter(Ticket.status == "open").count()
        in_progress_tickets = db.query(Ticket).filter(Ticket.status == "in_progress").count()
        resolved_tickets = db.query(Ticket).filter(Ticket.status == "resolved").count()
        closed_tickets = db.query(Ticket).filter(Ticket.status == "closed").count()
        
        # Average resolution time
        resolved_tickets_with_time = db.query(Ticket).filter(
            Ticket.resolved_at.isnot(None),
            Ticket.created_at.isnot(None)
        ).all()
        
        if resolved_tickets_with_time:
            total_resolution_time = sum([
                (ticket.resolved_at - ticket.created_at).total_seconds() / 3600
                for ticket in resolved_tickets_with_time
            ])
            avg_resolution_time = total_resolution_time / len(resolved_tickets_with_time)
        else:
            avg_resolution_time = 0.0
        
        # Tickets by category
        category_counts = db.query(
            Ticket.category, func.count(Ticket.id)
        ).group_by(Ticket.category).all()
        tickets_by_category = {cat or "Uncategorized": count for cat, count in category_counts}
        
        # Tickets by urgency
        urgency_counts = db.query(
            Ticket.urgency, func.count(Ticket.id)
        ).group_by(Ticket.urgency).all()
        tickets_by_urgency = {urg: count for urg, count in urgency_counts}
        
        # Tickets by source
        source_counts = db.query(
            Ticket.source, func.count(Ticket.id)
        ).group_by(Ticket.source).all()
        tickets_by_source = {src: count for src, count in source_counts}
        
        # AI processing rate
        ai_processed = db.query(Ticket).filter(Ticket.ai_processed == True).count()
        ai_processing_rate = (ai_processed / total_tickets * 100) if total_tickets > 0 else 0
        
        # Recent activity (last 24 hours)
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_tickets = db.query(Ticket).filter(
            Ticket.created_at >= recent_cutoff
        ).count()
        
        # Recent activity details
        recent_activity = []
        recent_interactions = db.query(TicketInteraction).join(Ticket).filter(
            TicketInteraction.created_at >= recent_cutoff
        ).order_by(desc(TicketInteraction.created_at)).limit(10).all()
        
        for interaction in recent_interactions:
            recent_activity.append({
                "ticket_number": interaction.ticket.ticket_number,
                "type": interaction.interaction_type,
                "timestamp": interaction.created_at.isoformat(),
                "summary": interaction.content[:100] + "..." if len(interaction.content) > 100 else interaction.content
            })
        
        analytics = AnalyticsResponse(
            total_tickets=total_tickets,
            open_tickets=open_tickets,
            in_progress_tickets=in_progress_tickets,
            resolved_tickets=resolved_tickets,
            closed_tickets=closed_tickets,
            average_resolution_time_hours=round(avg_resolution_time, 2),
            tickets_by_category=tickets_by_category,
            tickets_by_urgency=tickets_by_urgency,
            tickets_by_source=tickets_by_source,
            ai_processing_rate=round(ai_processing_rate, 2),
            recent_activity=recent_activity
        )
        
        logger.info("Generated analytics dashboard")
        return analytics
        
    except Exception as e:
        logger.error(f"Error generating analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate analytics")

@router.post("/search", response_model=List[SimilarTicketResponse])
async def search_tickets(
    search_request: SearchRequest,
    db: Session = Depends(get_db)
):
    """Search tickets using vector similarity"""
    try:
        if not vector_service.is_available():
            # Fallback to database text search
            query = db.query(Ticket)
            search_term = f"%{search_request.query}%"
            query = query.filter(
                or_(
                    Ticket.subject.ilike(search_term),
                    Ticket.description.ilike(search_term)
                )
            )
            
            if search_request.category_filter:
                query = query.filter(Ticket.category == search_request.category_filter)
            if search_request.status_filter:
                query = query.filter(Ticket.status == search_request.status_filter.value)
            
            tickets = query.limit(search_request.limit).all()
            
            results = [
                SimilarTicketResponse(
                    ticket_id=ticket.id,
                    ticket_number=ticket.ticket_number,
                    subject=ticket.subject,
                    category=ticket.category,
                    similarity_score=0.5,  # Default score for text search
                    status=ticket.status,
                    resolution_notes=ticket.resolution_notes
                )
                for ticket in tickets
            ]
            
            return results
        
        # Vector search
        similar_tickets = await vector_service.search_similar_tickets(
            search_request.query,
            limit=search_request.limit,
            category_filter=search_request.category_filter
        )
        
        results = []
        for similar in similar_tickets:
            ticket = db.query(Ticket).filter(Ticket.id == similar["ticket_id"]).first()
            if ticket:
                # Apply additional filters
                if search_request.status_filter and ticket.status != search_request.status_filter.value:
                    continue
                
                results.append(SimilarTicketResponse(
                    ticket_id=ticket.id,
                    ticket_number=ticket.ticket_number,
                    subject=ticket.subject,
                    category=ticket.category,
                    similarity_score=similar["similarity_score"],
                    status=ticket.status,
                    resolution_notes=ticket.resolution_notes
                ))
        
        logger.info(f"Search returned {len(results)} results for query: {search_request.query}")
        return results
        
    except Exception as e:
        logger.error(f"Error searching tickets: {e}")
        raise HTTPException(status_code=500, detail="Failed to search tickets")