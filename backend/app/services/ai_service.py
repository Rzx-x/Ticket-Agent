import anthropic
from typing import Dict, Any, Optional, List
import json
import re
import logging
from app.core.config import settings
from .language_detector import LanguageDetector

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        if not settings.ANTHROPIC_API_KEY:
            logger.warning("ANTHROPIC_API_KEY not configured. AI features will be limited.")
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            logger.info("AI Service initialized with Claude API")
        self.language_detector = LanguageDetector()
    
    def is_available(self) -> bool:
        return self.client is not None
    
    def detect_language(self, text: str) -> str:
        """Detect language and return simple string for backward compatibility"""
        try:
            lang_result = self.language_detector.detect_language(text)
            return lang_result.get("primary_language", "en")
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return "en"
    
    async def classify_ticket(self, subject: str, description: str) -> Dict[str, Any]:
        """Classify ticket using Claude with detailed analysis"""
        if not self.is_available():
            return self._get_fallback_classification()
        
        try:
            lang_info = self.language_detector.detect_language(description)
            
            prompt = f"""
            You are an expert IT support classifier for POWERGRID (Indian power company). 
            Analyze this support ticket and classify it accurately.
            
            Subject: {subject}
            Description: {description}
            Language Info: {lang_info}
            
            Respond with ONLY a valid JSON object:
            {{
                "category": "exact category name",
                "subcategory": "specific issue type", 
                "urgency": "low|medium|high|critical",
                "confidence": 0.85,
                "reasoning": "brief explanation",
                "suggested_keywords": ["keyword1", "keyword2"],
                "estimated_resolution_time": "2 hours"
            }}
            
            CATEGORIES (use exactly these):
            - Network: VPN, WiFi, internet, firewall, network drives, connectivity
            - Hardware: Computer, laptop, printer, monitor, keyboard, mouse, hardware failures
            - Software: Applications, installation, crashes, updates, licensing, MS Office
            - Email: Outlook, email issues, email setup, email access problems  
            - Account: Password reset, login issues, permissions, user account problems
            - Security: Antivirus, security alerts, suspicious activity, access control
            - Printer: Printing issues, printer setup, print queue, scanner problems
            - Telephony: Phone systems, extensions, call forwarding, conference calls
            - Other: Facility issues, non-IT requests, general inquiries
            
            URGENCY RULES:
            - critical: Complete system outage, security breach, many users affected
            - high: Important system down, urgent business impact, manager escalation
            - medium: Standard issues, some work impact, normal business request  
            - low: Minor issues, enhancement requests, general questions
            
            Consider Indian IT environment context and common POWERGRID issues.
            """
            
            response = await self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text.strip()
            
            # Extract JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                
                # Validate required fields
                result.setdefault('category', 'Other')
                result.setdefault('urgency', 'medium')
                result.setdefault('confidence', 0.0)
                result.setdefault('subcategory', 'General Issue')
                
                # Ensure confidence is float
                result['confidence'] = float(result.get('confidence', 0.0))
                
                logger.info(f"Ticket classified: {result['category']} - {result['urgency']} (confidence: {result['confidence']})")
                return result
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI classification JSON: {e}")
        except Exception as e:
            logger.error(f"AI classification error: {e}")
        
        return self._get_fallback_classification()
    
    async def generate_response(self, subject: str, description: str, 
                              language: str = "en", category: str = "Other",
                              user_name: str = None) -> str:
        """Generate contextual AI response"""
        if not self.is_available():
            return self._get_fallback_response(language, user_name)
        
        lang_info = self.detect_language(description)
        language = lang_info.get("primary_language", "en")
        
        # Greeting based on language and user
        greeting = f"Dear {user_name}," if user_name else "Hello,"
        if "hindi" in language.lower():
            greeting = f"नमस्ते {user_name}," if user_name else "नमस्ते,"
        
        lang_instruction = ""
        if "hindi" in language.lower() or language == "hi":
            lang_instruction = """
            IMPORTANT: Respond in natural Hinglish (Hindi + English mix) as used in Indian corporate IT environment.
            Use Hindi for greetings/courtesy and English for technical terms.
            Example: \"नमस्ते! आपकी VPN connectivity issue के लिए धन्यवाद...\" 
            """
        
        prompt = f"""
        You are a helpful IT support assistant at POWERGRID (Indian electricity board).
        A user has submitted this support ticket:
        
        Subject: {subject}
        Description: {description}
        Category: {category}
        User Language: {language}
        
        {lang_instruction}
        
        Generate a professional, empathetic response that:
        1. Starts with appropriate greeting
        2. Acknowledges their specific issue with empathy
        3. Provides immediate actionable troubleshooting steps (if applicable)
        4. Sets realistic expectations for resolution timeline
        5. Offers escalation path if needed
        6. Ends with professional closing
        
        RESPONSE GUIDELINES by Category:
        - Network/VPN: Check connection, restart network adapter, verify credentials
        - Hardware: Basic diagnostics, check cables, restart device, maintenance contact
        - Software: Check for updates, restart application, reinstall if needed
        - Email: Verify settings, check internet, restart Outlook, profile rebuild
        - Account: Self-service portal, security questions, manager approval process
        - Password: Reset link, security verification, temporary access
        
        Keep response concise but comprehensive. Use bullet points for steps.
        Include ticket number reference and support contact info.
        Be solution-oriented and professional.
        """
        
        try:
            response = await self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            ai_response = response.content[0].text.strip()
            logger.info(f"Generated AI response for {category} ticket")
            return ai_response
            
        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            return self._get_fallback_response(language, user_name)
    
    async def suggest_similar_solutions(self, ticket_content: str, 
                                      similar_tickets: List[Dict] = None) -> str:
        """Generate solution suggestions based on similar tickets"""
        if not self.is_available():
            return "Please refer to our knowledge base or contact IT support for detailed assistance."
        
        context = ""
        if similar_tickets:
            context = "\n\nSimilar resolved tickets for reference:\n"
            for i, ticket in enumerate(similar_tickets[:3], 1):
                context += f"{i}. {ticket.get('subject', 'N/A')}\n   Resolution: {ticket.get('resolution_notes', 'N/A')}\n"
        
        prompt = f"""
        Based on this IT support ticket, provide specific solution steps:
        
        Current Ticket: {ticket_content}
        {context}
        
        Provide a practical, step-by-step solution guide that:
        1. Lists immediate troubleshooting steps
        2. Includes common causes and fixes
        3. Mentions when to escalate to IT team
        4. Provides preventive measures if applicable
        
        Format as numbered steps. Keep it actionable and clear.
        Focus on solutions that work in Indian corporate IT environment.
        """
        
        try:
            response = await self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=800,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Solution suggestion failed: {e}")
            return "Please contact IT support for detailed troubleshooting assistance."
    
    def _get_fallback_classification(self) -> Dict[str, Any]:
        """Fallback classification when AI is unavailable"""
        return {
            "category": "Other",
            "subcategory": "General Inquiry", 
            "urgency": "medium",
            "confidence": 0.0,
            "reasoning": "AI classification unavailable",
            "suggested_keywords": [],
            "estimated_resolution_time": "4-6 hours"
        }
    
    def _get_fallback_response(self, language: str, user_name: str = None) -> str:
        """Fallback response when AI is unavailable"""
        if "hindi" in language.lower() or language == "hi":
            greeting = f"नमस्ते {user_name}," if user_name else "नमस्ते,"
            return f"""{greeting}

आपका support ticket हमें मिल गया है। हमारी IT team आपकी problem को जल्दी resolve करने की कोशिश करेगी।

आप expect कर सकते हैं:
- Response within 4-6 hours during business hours
- Regular updates on ticket progress  
- Professional solution और support

अगर urgent issue है तो please call our helpdesk directly.

धन्यवाद,
POWERGRID IT Support Team"""
        else:
            greeting = f"Dear {user_name}," if user_name else "Hello,"
            return f"""{greeting}

Thank you for contacting POWERGRID IT Support. We have received your ticket and our technical team will review it promptly.

What to expect:
- Response within 4-6 hours during business hours
- Regular updates on resolution progress
- Professional support throughout the process

For urgent issues requiring immediate attention, please contact our helpdesk directly.

Best regards,
POWERGRID IT Support Team"""

# Global AI service instance
ai_service = AIService()
