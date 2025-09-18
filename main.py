from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging
import os
from datetime import datetime, timedelta
import uuid
from typing import List

# Local imports
from db.database import get_db, create_tables
from db.models import Ticket, TicketResponse, TicketAnalytics, KnowledgeBase
from ai.language_detector import language_detector
from ai.claude_service import claude_service
from ai.vector_database import vector_store
from schemas import TicketCreate, TicketResponse as TicketResponseSchema, TicketUpdate, TicketStatusEnum, TicketUrgencyEnum
from scripts.ticket_services import ticket_service
from scripts.analytics_services import analytics_service

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="OmniDesk AI - IT Ticket Management",
    description="Smart IT ticket management system with AI classification and response generation",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    try:
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Ticket endpoints
@app.post("/api/tickets", response_model=TicketResponseSchema)
async def create_ticket(
    ticket_data: TicketCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new ticket with AI processing"""
    try:
        # Create ticket in database
        ticket = await ticket_service.create_ticket(db, ticket_data)
        
        # Background AI processing
        background_tasks.add_task(
            process_ticket_ai,
            ticket.id,
            ticket_data.description
        )
        
        return TicketResponseSchema.from_orm(ticket)
        
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tickets", response_model=List[TicketResponseSchema])
async def get_tickets(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    category: str = None,
    db: Session = Depends(get_db)
):
    """Get tickets with optional filtering"""
    try:
        tickets = await ticket_service.get_tickets(db, skip, limit, status, category)
        return [TicketResponseSchema.from_orm(ticket) for ticket in tickets]
        
    except Exception as e:
        logger.error(f"Error fetching tickets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tickets/{ticket_id}", response_model=TicketResponseSchema)
async def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    """Get specific ticket by ID"""
    try:
        ticket = await ticket_service.get_ticket_by_id(db, ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        return TicketResponseSchema.from_orm(ticket)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/tickets/{ticket_id}", response_model=TicketResponseSchema)
async def update_ticket(
    ticket_id: str,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db)
):
    """Update ticket status and details"""
    try:
        ticket = await ticket_service.update_ticket(db, ticket_id, ticket_update)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        return TicketResponseSchema.from_orm(ticket)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics endpoints

@app.get("/api/analytics/dashboard")
async def get_dashboard_analytics(db: Session = Depends(get_db)):
    """Get dashboard analytics"""
    try:
        analytics = await analytics_service.get_dashboard_metrics(db)
        return analytics
        
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
async def process_ticket_ai(ticket_id: str, description: str):
    """
    Perform AI processing on a newly created ticket in the background.
    This includes language detection, classification, and AI response generation.
    """
    db = None
    try:
        db = next(get_db())
        
        # 1. Language Detection
        language_info = await language_detector.detect_language(description)
        logger.info(f"Language detection for ticket {ticket_id}: {language_info}")
        
        # 2. Ticket Classification
        classification = await claude_service.classify_ticket(description, language_info)
        logger.info(f"Classification for ticket {ticket_id}: {classification}")
        
        # 3. Generate AI Response / Suggestion
        # First, try to find relevant knowledge base articles
        kb_articles = await vector_store.search_knowledge_base(description, k=2)
        
        ai_response = await claude_service.generate_response(
            description,
            classification.get("category"),
            classification.get("subcategory"),
            kb_articles,
            language_info
        )
        logger.info(f"AI response for ticket {ticket_id}: {ai_response}")
        
        # 4. Update ticket with AI data
        await ticket_service.update_ticket_ai_data(
            db,
            ticket_id,
            language_info,
            classification,
            ai_response
        )
        
        logger.info(f"AI processing completed for ticket: {ticket_id}")
        
    except Exception as e:
        logger.error(f"Error in AI processing for ticket {ticket_id}: {e}")
    finally:
        if db:
            db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

```

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

### 5.2 Pydantic Schemas (`schemas.py`)
```python
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