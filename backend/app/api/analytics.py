from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.services.analytics_services import analytics_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/dashboard")
async def get_dashboard_analytics(db: Session = Depends(get_db)):
    """Get dashboard analytics"""
    try:
        analytics = await analytics_service.get_dashboard_metrics(db)
        return analytics
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))