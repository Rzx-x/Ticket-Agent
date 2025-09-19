import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import logging
from typing import Optional, List
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.is_configured = all([self.username, self.password])
    
    async def send_ticket_response(self, to_email: str, ticket_number: str, 
                                 subject: str, content: str, 
                                 attachments: List[str] = None) -> bool:
        """Send ticket response via email"""
        if not self.is_configured:
            logger.warning("Email service not configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.username
            msg["To"] = to_email
            msg["Subject"] = f"Re: [{ticket_number}] {subject}"
            
            # Email body
            body = f"""
Dear User,

Thank you for contacting POWERGRID IT Support.

Ticket Number: {ticket_number}
Status: Response Provided

{content}

If you need further assistance, please reply to this email or contact our helpdesk.

Best regards,
POWERGRID IT Support Team
Email: {self.username}
            """.strip()
            
            msg.attach(MIMEText(body, "plain"))
            
            # Add attachments if any
            if attachments:
                for file_path in attachments:
                    try:
                        with open(file_path, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {file_path.split("/")[-1]}'
                            )
                            msg.attach(part)
                    except Exception as e:
                        logger.warning(f"Failed to attach file {file_path}: {e}")
            
            # Send email
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                start_tls=True,
                username=self.username,
                password=self.password
            )
            
            logger.info(f"Email sent successfully to {to_email} for ticket {ticket_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    async def send_notification(self, to_emails: List[str], subject: str, 
                              content: str) -> bool:
        """Send notification email to multiple recipients"""
        if not self.is_configured:
            return False
        
        try:
            msg = MIMEMultipart()
            msg["From"] = self.username
            msg["To"] = ", ".join(to_emails)
            msg["Subject"] = subject
            
            msg.attach(MIMEText(content, "plain"))
            
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                start_tls=True,
                username=self.username,
                password=self.password
            )
            
            logger.info(f"Notification sent to {len(to_emails)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False

email_service = EmailService()