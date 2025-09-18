from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Dict, List, Any
from datetime import datetime, timedelta
import logging

from db.models import Ticket, TicketAnalytics, TicketResponse, TicketStatus, TicketUrgency

logger = logging.getLogger(__name__)

class AnalyticsService:
    
    async def get_dashboard_metrics(self, db: Session) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics"""
        try:
            # Basic counts
            total_tickets = db.query(Ticket).count()
            open_tickets = db.query(Ticket).filter(
                Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS])
            ).count()
            resolved_tickets = db.query(Ticket).filter(
                Ticket.status == TicketStatus.RESOLVED
            ).count()
            
            # Average resolution time
            avg_resolution = db.query(
                func.avg(TicketAnalytics.resolution_time_minutes)
            ).filter(
                TicketAnalytics.resolution_time_minutes.isnot(None)
            ).scalar() or 0
            
            # Tickets by category
            category_stats = db.query(
                Ticket.category,
                func.count(Ticket.id).label('count')
            ).filter(
                Ticket.category.isnot(None)
            ).group_by(Ticket.category).all()
            
            tickets_by_category = {cat: count for cat, count in category_stats}
            
            # Tickets by urgency
            urgency_stats = db.query(
                Ticket.urgency,
                func.count(Ticket.id).label('count')
            ).filter(
                Ticket.urgency.isnot(None)
            ).group_by(Ticket.urgency).all()
            
            tickets_by_urgency = {str(urg): count for urg, count in urgency_stats}
            
            # AI success rate
            total_ai_responses = db.query(TicketAnalytics).filter(
                TicketAnalytics.auto_resolution_attempted == True
            ).count()
            
            successful_ai_responses = db.query(TicketAnalytics).filter(
                and_(
                    TicketAnalytics.auto_resolution_attempted == True,
                    TicketAnalytics.auto_resolution_successful == True
                )
            ).count()
            
            ai_success_rate = (successful_ai_responses / total_ai_responses * 100) if total_ai_responses > 0 else 0
            
            # Recent tickets (last 10)
            recent_tickets = db.query(Ticket).order_by(
                Ticket.created_at.desc()
            ).limit(10).all()
            
            # Today's stats
            today = datetime.utcnow().date()
            today_tickets = db.query(Ticket).filter(
                func.date(Ticket.created_at) == today
            ).count()
            
            # Response time stats
            response_times = db.query(TicketAnalytics.first_response_time_minutes).filter(
                TicketAnalytics.first_response_time_minutes.isnot(None)
            ).all()
            
            avg_first_response = sum(rt[0] for rt in response_times) / len(response_times) if response_times else 0
            
            return {
                "overview": {
                    "total_tickets": total_tickets,
                    "open_tickets": open_tickets,
                    "resolved_tickets": resolved_tickets,
                    "today_tickets": today_tickets,
                    "average_resolution_time_hours": round(avg_resolution / 60, 2),
                    "average_first_response_time_minutes": round(avg_first_response, 2),
                    "ai_success_rate": round(ai_success_rate, 2)
                },
                "distribution": {
                    "tickets_by_category": tickets_by_category,
                    "tickets_by_urgency": tickets_by_urgency
                },
                "recent_activity": {
                    "recent_tickets": [
                        {
                            "id": str(ticket.id),
                            "ticket_number": ticket.ticket_number,
                            "title": ticket.title,
                            "status": ticket.status,
                            "urgency": ticket.urgency,
                            "category": ticket.category,
                            "created_at": ticket.created_at.isoformat(),
                            "user_name": ticket.user_name
                        }
                        for ticket in recent_tickets
                    ]
                },
                "performance": {
                    "resolution_rate": round((resolved_tickets / total_tickets * 100), 2) if total_tickets > 0 else 0,
                    "escalation_rate": round(
                        (db.query(Ticket).filter(Ticket.status == TicketStatus.ESCALATED).count() / total_tickets * 100), 2
                    ) if total_tickets > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard metrics: {e}")
            raise
    
    async def get_trend_analysis(self, db: Session, days: int = 30) -> Dict[str, Any]:
        """Get trend analysis for specified number of days"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Daily ticket creation trend
            daily_tickets = db.query(
                func.date(Ticket.created_at).label('date'),
                func.count(Ticket.id).label('count')
            ).filter(
                Ticket.created_at >= start_date
            ).group_by(
                func.date(Ticket.created_at)
            ).order_by('date').all()
            
            # Daily resolution trend
            daily_resolutions = db.query(
                func.date(Ticket.resolved_at).label('date'),
                func.count(Ticket.id).label('count')
            ).filter(
                and_(
                    Ticket.resolved_at >= start_date,
                    Ticket.resolved_at.isnot(None)
                )
            ).group_by(
                func.date(Ticket.resolved_at)
            ).order_by('date').all()
            
            # Category trends
            category_trends = db.query(
                Ticket.category,
                func.count(Ticket.id).label('count'),
                func.avg(TicketAnalytics.resolution_time_minutes).label('avg_resolution')
            ).join(TicketAnalytics).filter(
                Ticket.created_at >= start_date
            ).group_by(Ticket.category).all()
            
            # Language distribution
            language_dist = db.query(
                Ticket.detected_language,
                func.count(Ticket.id).label('count')
            ).filter(
                and_(
                    Ticket.created_at >= start_date,
                    Ticket.detected_language.isnot(None)
                )
            ).group_by(Ticket.detected_language).all()
            
            return {
                "period": {
                    "start_date": start_date.date().isoformat(),
                    "end_date": datetime.utcnow().date().isoformat(),
                    "days": days
                },
                "daily_trends": {
                    "ticket_creation": [
                        {"date": str(date), "count": count}
                        for date, count in daily_tickets
                    ],
                    "ticket_resolution": [
                        {"date": str(date), "count": count}
                        for date, count in daily_resolutions
                    ]
                },
                "category_analysis": [
                    {
                        "category": category,
                        "count": count,
                        "avg_resolution_hours": round((avg_resolution or 0) / 60, 2)
                    }
                    for category, count, avg_resolution in category_trends
                ],
                "language_distribution": [
                    {"language": lang, "count": count}
                    for lang, count in language_dist
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting trend analysis: {e}")
            raise

# Global instance
analytics_service = AnalyticsService()