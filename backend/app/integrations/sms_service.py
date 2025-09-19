from twilio.rest import Client
from typing import Optional
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class SMSService:
    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.phone_number = settings.TWILIO_PHONE_NUMBER
        self.is_configured = all([self.account_sid, self.auth_token, self.phone_number])
        
        if self.is_configured:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None
    
    async def send_ticket_response(self, to_phone: str, ticket_number: str, 
                                 message: str) -> bool:
        """Send ticket response via SMS"""
        if not self.is_configured:
            logger.warning("SMS service not configured")
            return False
        
        try:
            # Format message for SMS
            sms_content = f"POWERGRID IT: Ticket {ticket_number} - {message[:100]}... For full response, check email or portal."
            
            message = self.client.messages.create(
                body=sms_content,
                from_=self.phone_number,
                to=to_phone
            )
            
            logger.info(f"SMS sent successfully to {to_phone} for ticket {ticket_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_phone}: {e}")
            return False
    
    async def send_urgent_alert(self, to_phone: str, ticket_number: str) -> bool:
        """Send urgent ticket alert via SMS"""
        if not self.is_configured:
            return False
        
        try:
            sms_content = f"URGENT: POWERGRID IT Ticket {ticket_number} requires immediate attention. Please check the system."
            
            message = self.client.messages.create(
                body=sms_content,
                from_=self.phone_number,
                to=to_phone
            )
            
            logger.info(f"Urgent alert sent to {to_phone} for ticket {ticket_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send urgent alert: {e}")
            return False

sms_service = SMSService()