import httpx
from typing import Dict, List, Optional, AsyncGenerator
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class GLPIIntegration:
    def __init__(self):
        self.base_url = settings.GLPI_URL
        self.user_token = settings.GLPI_USER_TOKEN
        self.app_token = settings.GLPI_APP_TOKEN
        self.session_token = None
        self.is_configured = all([self.base_url, self.user_token, self.app_token])
    
    async def authenticate(self) -> bool:
        """Authenticate with GLPI and get session token"""
        if not self.is_configured:
            logger.warning("GLPI not fully configured")
            return False
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"user_token {self.user_token}",
            "App-Token": self.app_token
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/initSession", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    self.session_token = data.get("session_token")
                    logger.info("GLPI authentication successful")
                    return True
                else:
                    logger.error(f"GLPI authentication failed: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"GLPI authentication error: {e}")
        
        return False
    
    async def fetch_tickets(self, limit: int = 50) -> AsyncGenerator[Dict, None]:
        """Fetch tickets from GLPI"""
        if not await self.authenticate():
            return
        
        headers = {
            "Session-Token": self.session_token,
            "App-Token": self.app_token,
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Fetch tickets with pagination
                response = await client.get(
                    f"{self.base_url}/Ticket",
                    headers=headers,
                    params={"range": f"0-{limit-1}", "expand_dropdowns": "true"}
                )
                
                if response.status_code == 200:
                    tickets = response.json()
                    
                    for ticket in tickets:
                        yield {
                            "external_id": str(ticket.get("id")),
                            "source": "glpi",
                            "subject": ticket.get("name", "No Subject"),
                            "description": ticket.get("content", ""),
                            "user_email": ticket.get("users_id_recipient", "unknown@glpi.local"),
                            "status": self._map_glpi_status(ticket.get("status")),
                            "urgency": self._map_glpi_urgency(ticket.get("urgency")),
                            "category": ticket.get("itilcategories_id_name", "Other"),
                            "created_at": ticket.get("date"),
                            "updated_at": ticket.get("date_mod")
                        }
                        
        except Exception as e:
            logger.error(f"Error fetching GLPI tickets: {e}")
    
    async def create_ticket(self, ticket_data: Dict) -> Optional[str]:
        """Create ticket in GLPI"""
        if not await self.authenticate():
            return None
        
        headers = {
            "Session-Token": self.session_token,
            "App-Token": self.app_token,
            "Content-Type": "application/json"
        }
        
        glpi_data = {
            "input": {
                "name": ticket_data.get("subject"),
                "content": ticket_data.get("description"),
                "urgency": self._map_urgency_to_glpi(ticket_data.get("urgency", "medium")),
                "users_id_recipient": ticket_data.get("user_email")
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/Ticket",
                    headers=headers,
                    json=glpi_data
                )
                
                if response.status_code == 201:
                    result = response.json()
                    ticket_id = result.get("id")
                    logger.info(f"Created GLPI ticket: {ticket_id}")
                    return str(ticket_id)
                    
        except Exception as e:
            logger.error(f"Error creating GLPI ticket: {e}")
        
        return None
    
    def _map_glpi_status(self, glpi_status: int) -> str:
        """Map GLPI status to our status"""
        status_map = {
            1: "open",          # New
            2: "in_progress",   # Processing (assigned)
            3: "in_progress",   # Processing (planned)
            4: "pending",       # Pending
            5: "resolved",      # Solved
            6: "closed"         # Closed
        }
        return status_map.get(glpi_status, "open")
    
    def _map_glpi_urgency(self, glpi_urgency: int) -> str:
        """Map GLPI urgency to our urgency"""
        urgency_map = {
            1: "low",       # Very low
            2: "low",       # Low  
            3: "medium",    # Medium
            4: "high",      # High
            5: "critical"   # Very high
        }
        return urgency_map.get(glpi_urgency, "medium")
    
    def _map_urgency_to_glpi(self, urgency: str) -> int:
        """Map our urgency to GLPI urgency"""
        urgency_map = {
            "low": 2,
            "medium": 3,
            "high": 4,
            "critical": 5
        }
        return urgency_map.get(urgency, 3)

glpi_service = GLPIIntegration()