"""
Enhanced Tickets API with Production-Ready Error Handling
Provides comprehensive ticket management endpoints with advanced AI integration,
real-time updates, and robust validation.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, WebSocket, Query
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional, Dict, Any
import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
import json

# Import enhanced schemas
from app.schemas.enhanced_schemas import (
    TicketCreateRequest, TicketUpdateRequest, TicketDetailResponse,
    PaginatedTicketResponse, SearchRequest, AnalyticsResponse,
    SuccessResponse, ErrorResponse, ValidationErrorResponse,
    TicketStatus, TicketUrgency, WebSocketMessage, TicketUpdateMessage
)

# Import AI services
from ai.services.ai_engine import get_ai_engine, ClassificationResult
from ai.services.vector_engine import get_vector_engine, VectorSearchConfig

# Import database and dependencies
from app.core.database import get_db
from app.core.exceptions import (
    OmniDeskBaseException, ValidationError, NotFoundError, 
    DatabaseError, AIServiceError, RateLimitExceeded
)

# Import models
from db.models import Ticket, TicketResponse as DBTicketResponse, TicketAnalytics

# Import utilities
from app.core.security import get_current_user, require_permissions
from app.core.rate_limiter import rate_limit
from app.core.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/tickets", tags=["Tickets"])

# WebSocket manager for real-time updates
websocket_manager = WebSocketManager()

# Request ID tracking
def generate_request_id() -> str:
    """Generate unique request ID for tracking"""
    return str(uuid.uuid4())

def get_request_id(request: Request) -> str:
    """Get or create request ID"""
    return getattr(request.state, 'request_id', generate_request_id())

# Enhanced error handlers
def handle_validation_error(e: Exception, request_id: str) -> JSONResponse:
    """Handle validation errors with detailed information"""
    error_details = []
    field_errors = {}
    
    if hasattr(e, 'errors'):
        for error in e.errors():
            field = '.'.join(str(loc) for loc in error['loc'])
            message = error['msg']
            error_details.append({
                "code": "VALIDATION_ERROR",
                "message": message,
                "field": field,
                "context": {"input": error.get('input')}
            })
            
            if field not in field_errors:
                field_errors[field] = []
            field_errors[field].append(message)
    
    response = ValidationErrorResponse(
        message="Request validation failed",
        details=error_details,
        field_errors=field_errors,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=422,
        content=response.model_dump()
    )

def handle_database_error(e: Exception, request_id: str) -> JSONResponse:
    """Handle database errors"""
    logger.error(f"Database error in request {request_id}: {e}")
    
    response = ErrorResponse(
        message="Database operation failed",
        details=[{
            "code": "DATABASE_ERROR",
            "message": "An error occurred while processing your request",
            "context": {"error_type": type(e).__name__}
        }],
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=500,
        content=response.model_dump()
    )

def handle_ai_service_error(e: Exception, request_id: str) -> JSONResponse:
    """Handle AI service errors"""
    logger.error(f"AI service error in request {request_id}: {e}")
    
    response = ErrorResponse(
        message="AI service temporarily unavailable",
        details=[{
            "code": "AI_SERVICE_ERROR", 
            "message": "AI processing failed, using fallback response",
            "context": {"service": "classification"}
        }],
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=503,
        content=response.model_dump()
    )

# Enhanced endpoints
@router.post(
    "/",
    response_model=SuccessResponse,
    status_code=201,
    summary="Create a new support ticket",
    description="""
    Create a new support ticket with AI-powered classification and auto-response.
    
    Features:
    - Automatic language detection (English/Hindi/Mixed)
    - AI-powered category and urgency classification
    - Intelligent auto-response generation
    - Real-time notifications to relevant stakeholders
    - Vector embedding for semantic search
    """,
    responses={
        201: {"description": "Ticket created successfully"},
        400: {"description": "Invalid request data", "model": ValidationErrorResponse},
        429: {"description": "Rate limit exceeded"},
        503: {"description": "Service temporarily unavailable"}
    }
)
async def create_ticket(
    ticket_request: TicketCreateRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new support ticket with enhanced AI processing"""
    request_id = generate_request_id()
    request.state.request_id = request_id
    
    start_time = time.time()
    
    try:
        # Rate limiting
        await rate_limit("create_ticket", current_user.get("user_id", "anonymous"))
        
        # Generate ticket number
        ticket_number = f"TKT-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        # Initialize AI engine
        ai_engine = get_ai_engine({
            'anthropic_api_key': request.app.state.config.ANTHROPIC_API_KEY,
            'enable_gpu': True,
            'features': ['multilingual']
        })
        
        # AI Classification with enhanced processing
        classification_response = await ai_engine.classify_ticket_advanced(
            subject=ticket_request.title,
            description=ticket_request.description,
            user_context={
                'department': ticket_request.user_info.department,
                'role': ticket_request.user_info.role,
                'previous_tickets': 0  # Could be enhanced with history
            }
        )
        
        classification = classification_response.result
        
        # Create ticket in database
        db_ticket = Ticket(
            ticket_number=ticket_number,
            title=ticket_request.title,
            description=ticket_request.description,
            original_text=f"{ticket_request.title}\\n{ticket_request.description}",
            source=ticket_request.source.value,
            user_name=ticket_request.user_info.name,
            user_email=ticket_request.user_info.email,
            user_department=ticket_request.user_info.department,
            
            # AI Classification results
            category=classification.category,
            subcategory=classification.subcategory,
            urgency=classification.urgency.value,
            ai_confidence=classification.confidence,
            
            # Language detection
            detected_language=classification.language_detected,
            is_mixed_language=classification.is_mixed_language,
            
            status=TicketStatus.OPEN.value,
            extra_metadata={
                'ai_reasoning': classification.reasoning,
                'keywords': classification.keywords,
                'estimated_resolution_time': classification.estimated_resolution_time,
                'processing_time_ms': classification_response.processing_time * 1000,
                'gpu_accelerated': classification_response.gpu_accelerated,
                'request_id': request_id,
                'external_id': ticket_request.external_id,
                'context': ticket_request.context
            }
        )
        
        db.add(db_ticket)
        db.flush()  # Get the ID without committing
        
        # Create analytics record
        analytics = TicketAnalytics(
            ticket_id=db_ticket.id,
            ai_accuracy_score=classification.confidence,
            auto_resolution_attempted=True
        )
        db.add(analytics)
        
        # Generate AI response
        ai_response_text = await ai_engine.generate_ai_response(
            subject=ticket_request.title,
            description=ticket_request.description,
            category=classification.category,
            language=classification.language_detected,
            user_name=ticket_request.user_info.name
        )
        
        # Save AI response
        if ai_response_text:
            ai_response = DBTicketResponse(
                ticket_id=db_ticket.id,
                response_text=ai_response_text,
                is_ai_response=True,
                is_auto_response=True,
                ai_model_used="ensemble",
                confidence_score=classification.confidence,
                response_time_ms=int((time.time() - start_time) * 1000),
                responder_name="OmniDesk AI Assistant"
            )
            db.add(ai_response)
        
        # Commit transaction
        db.commit()
        
        # Background tasks
        background_tasks.add_task(
            process_ticket_background,
            ticket_id=str(db_ticket.id),
            ticket_content=f"{ticket_request.title}\\n{ticket_request.description}",
            classification=classification,
            request_id=request_id
        )
        
        # Real-time notification
        await websocket_manager.broadcast_ticket_update(
            ticket_id=str(db_ticket.id),
            update_type="created",
            data={
                "ticket_number": ticket_number,
                "title": ticket_request.title,
                "urgency": classification.urgency.value,
                "category": classification.category,
                "user": ticket_request.user_info.name
            },
            affected_users=[ticket_request.user_info.email]
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        response = SuccessResponse(
            message=f"Ticket {ticket_number} created successfully",
            data={
                "ticket_id": str(db_ticket.id),
                "ticket_number": ticket_number,
                "classification": {
                    "category": classification.category,
                    "urgency": classification.urgency.value,
                    "confidence": classification.confidence,
                    "estimated_resolution": classification.estimated_resolution_time
                },
                "ai_response_provided": bool(ai_response_text),
                "processing_time_ms": processing_time
            },
            request_id=request_id
        )
        
        logger.info(f"Ticket {ticket_number} created successfully in {processing_time:.2f}ms")
        return response
        
    except ValidationError as e:
        return handle_validation_error(e, request_id)
    except SQLAlchemyError as e:
        db.rollback()
        return handle_database_error(e, request_id)
    except AIServiceError as e:
        # Continue without AI features
        logger.warning(f"AI service unavailable: {e}")
        # Implement fallback ticket creation logic here
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=429,
            detail={
                "message": "Rate limit exceeded",
                "retry_after": e.retry_after,
                "request_id": request_id
            }
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating ticket: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Internal server error",
                "request_id": request_id
            }
        )

@router.get(
    "/",
    response_model=PaginatedTicketResponse,
    summary="List tickets with advanced filtering and search",
    description="""
    Retrieve tickets with powerful filtering, sorting, and semantic search capabilities.
    
    Features:
    - AI-powered semantic search
    - Advanced filtering by status, category, urgency, date ranges
    - Real-time results with WebSocket notifications
    - Performance-optimized pagination
    """,
    responses={
        200: {"description": "Tickets retrieved successfully"},
        400: {"description": "Invalid query parameters"}
    }
)
async def list_tickets(
    request: Request,
    limit: int = Query(default=10, le=100, ge=1, description="Number of tickets per page"),
    offset: int = Query(default=0, ge=0, description="Number of tickets to skip"),
    status: Optional[TicketStatus] = Query(None, description="Filter by ticket status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    urgency: Optional[TicketUrgency] = Query(None, description="Filter by urgency"),
    search: Optional[str] = Query(None, min_length=3, max_length=500, description="Search query"),
    semantic_search: bool = Query(default=True, description="Use AI semantic search"),
    assigned_to: Optional[str] = Query(None, description="Filter by assigned agent"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    sort_by: str = Query(default="created_at", description="Sort field"),
    sort_order: str = Query(default="desc", regex="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List tickets with enhanced search and filtering"""
    request_id = generate_request_id()
    start_time = time.time()
    
    try:
        # Build query
        query = db.query(Ticket)
        
        # Apply filters
        if status:
            query = query.filter(Ticket.status == status.value)
        if category:
            query = query.filter(Ticket.category.ilike(f"%{category}%"))
        if urgency:
            query = query.filter(Ticket.urgency == urgency.value)
        if assigned_to:
            query = query.filter(Ticket.assigned_to.ilike(f"%{assigned_to}%"))
        if date_from:
            query = query.filter(Ticket.created_at >= date_from)
        if date_to:
            query = query.filter(Ticket.created_at <= date_to)
        
        # Apply search
        if search:
            if semantic_search:
                # Use AI-powered semantic search
                similar_tickets = await search_tickets_semantic(
                    search, limit=limit, offset=offset, filters={
                        'status': status.value if status else None,
                        'category': category,
                        'urgency': urgency.value if urgency else None
                    }
                )
                tickets = similar_tickets
            else:
                # Traditional text search
                search_filter = f"%{search}%"
                query = query.filter(
                    (Ticket.title.ilike(search_filter)) |
                    (Ticket.description.ilike(search_filter))
                )
        
        # Apply sorting
        sort_column = getattr(Ticket, sort_by, Ticket.created_at)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        if not (search and semantic_search):
            tickets = query.offset(offset).limit(limit).all()
        
        # Convert to response format
        ticket_responses = []
        for ticket in tickets:
            # Get latest responses
            latest_responses = db.query(DBTicketResponse).filter(
                DBTicketResponse.ticket_id == ticket.id
            ).order_by(DBTicketResponse.created_at.desc()).limit(5).all()
            
            ticket_response = TicketDetailResponse(
                id=ticket.id,
                ticket_number=ticket.ticket_number,
                title=ticket.title,
                description=ticket.description,
                status=TicketStatus(ticket.status),
                urgency=TicketUrgency(ticket.urgency),
                category=ticket.category,
                subcategory=ticket.subcategory or "General",
                source=ticket.source,
                user_info={
                    "name": ticket.user_name,
                    "email": ticket.user_email,
                    "department": ticket.user_department,
                    "role": "user"
                },
                assigned_to=ticket.assigned_to,
                created_at=ticket.created_at,
                updated_at=ticket.updated_at,
                resolved_at=ticket.resolved_at,
                responses=[
                    {
                        "id": resp.id,
                        "ticket_id": resp.ticket_id,
                        "response_text": resp.response_text,
                        "response_type": "ai_auto" if resp.is_ai_response else "human",
                        "is_internal": False,
                        "responder_name": resp.responder_name,
                        "responder_role": "agent",
                        "created_at": resp.created_at
                    } for resp in latest_responses
                ]
            )
            ticket_responses.append(ticket_response)
        
        processing_time = (time.time() - start_time) * 1000
        
        response = PaginatedTicketResponse(
            items=ticket_responses,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total
        )
        
        logger.info(f"Listed {len(ticket_responses)} tickets in {processing_time:.2f}ms")
        return response
        
    except Exception as e:
        logger.error(f"Error listing tickets: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to retrieve tickets",
                "request_id": request_id
            }
        )

async def search_tickets_semantic(query: str, limit: int, offset: int, filters: Dict) -> List[Ticket]:
    """Perform semantic search using vector engine"""
    try:
        vector_engine = await get_vector_engine()
        
        search_results = await vector_engine.search_similar_advanced(
            query_text=query,
            collection_purpose="tickets",
            limit=limit + offset,  # Get more to handle offset
            filters=filters,
            min_score=0.6
        )
        
        # Apply offset and limit
        paginated_results = search_results[offset:offset + limit]
        
        # Convert back to Ticket objects (simplified for example)
        # In production, you'd fetch from database using the IDs
        tickets = []
        for result in paginated_results:
            # This would be replaced with actual database lookup
            ticket_id = result.id
            # tickets.append(db.query(Ticket).filter(Ticket.id == ticket_id).first())
        
        return tickets
        
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        return []

async def process_ticket_background(ticket_id: str, ticket_content: str, classification: ClassificationResult, request_id: str):
    """Background processing for tickets"""
    try:
        # Add to vector database
        vector_engine = await get_vector_engine()
        await vector_engine.add_vectors_batch(
            collection_purpose="tickets",
            vectors_data=[{
                'id': ticket_id,
                'text': ticket_content,
                'metadata': {
                    'category': classification.category,
                    'urgency': classification.urgency.value,
                    'language': classification.language_detected,
                    'confidence': classification.confidence,
                    'request_id': request_id
                }
            }]
        )
        
        # Search for similar tickets for knowledge transfer
        similar_tickets = await vector_engine.search_similar_advanced(
            query_text=ticket_content,
            collection_purpose="tickets", 
            limit=5,
            filters={'category': classification.category},
            min_score=0.8
        )
        
        logger.info(f"Background processing completed for ticket {ticket_id}")
        
    except Exception as e:
        logger.error(f"Background processing failed for ticket {ticket_id}: {e}")

# WebSocket endpoint for real-time updates
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time ticket updates"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "subscribe":
                # Subscribe to specific ticket updates
                ticket_ids = message.get("ticket_ids", [])
                await websocket_manager.subscribe_to_tickets(websocket, ticket_ids)
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket_manager.disconnect(websocket)

# Export router
__all__ = ['router']