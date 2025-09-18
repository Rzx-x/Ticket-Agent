import os
import json
import asyncio
from anthropic import Anthropic
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ClaudeAIService:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-3-sonnet-20240229"
        
        # Ticket categories for classification
        self.categories = {
            "Network": ["VPN", "Internet", "WiFi", "Connectivity"],
            "Hardware": ["Laptop", "Desktop", "Printer", "Monitor", "Mouse", "Keyboard"],
            "Software": ["Application", "Installation", "Update", "License"],
            "Email": ["Outlook", "Exchange", "Mailbox", "Attachment"],
            "Security": ["Password", "Access", "Login", "Virus", "Malware"],
            "Server": ["Database", "Application Server", "File Server", "Backup"],
            "Mobile": ["Phone", "Tablet", "App", "Sync"],
            "Other": ["General", "Request", "Question"]
        }
    
    async def classify_ticket(self, ticket_text: str, language_info: Dict) -> Dict[str, Any]:
        """
        Classify ticket using Claude API
        Returns category, urgency, and confidence scores
        """
        try:
            prompt = self._build_classification_prompt(ticket_text, language_info)
            
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse Claude's response
            classification = self._parse_classification_response(response.content[0].text)
            
            logger.info(f"Ticket classified: {classification}")
            return classification
            
        except Exception as e:
            logger.error(f"Error in ticket classification: {e}")
            return self._default_classification()
    
    async def generate_response(self, ticket_text: str, classification: Dict, language_info: Dict, similar_tickets: List = None) -> Dict[str, Any]:
        """
        Generate AI response to ticket
        Returns response text, confidence, and metadata
        """
        try:
            prompt = self._build_response_prompt(ticket_text, classification, language_info, similar_tickets)
            
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_data = self._parse_response(response.content[0].text, language_info)
            
            logger.info(f"AI response generated: {response_data['confidence']}")
            return response_data
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self._default_response(language_info)
    
    def _build_classification_prompt(self, ticket_text: str, language_info: Dict) -> str:
        """Build prompt for ticket classification"""
        categories_str = json.dumps(self.categories, indent=2)
        
        return f"""
You are an IT helpdesk AI assistant for POWERGRID employees. Classify the following ticket:

Ticket Text: "{ticket_text}"
Language Info: {language_info}

Available Categories and Subcategories:
{categories_str}

Please classify this ticket and respond with a JSON object containing:
1. "category": Main category from the list above
2. "subcategory": Specific subcategory or create appropriate one
3. "urgency": "low", "medium", "high", or "critical"
4. "confidence": Score from 0.0 to 1.0
5. "reasoning": Brief explanation of your classification
6. "keywords": List of key technical terms identified

Consider:
- Language mixing (Hindi/English) is common
- POWERGRID context (power utility company)
- Technical terminology in both languages
- Urgency based on business impact

Response format: {{"category": "...", "subcategory": "...", "urgency": "...", "confidence": 0.0, "reasoning": "...", "keywords": []}}
"""

    def _build_response_prompt(self, ticket_text: str, classification: Dict, language_info: Dict, similar_tickets: List = None) -> str:
        """Build prompt for response generation"""
        language = language_info.get("primary_language", "english")
        is_mixed = language_info.get("is_mixed", False)
        
        similar_context = ""
        if similar_tickets:
            similar_context = "Similar previous tickets:\n" + "\n".join([
                f"- {ticket.get('text', '')[:100]}..." for ticket in similar_tickets[:3]
            ])
        
        return f"""
You are an IT helpdesk AI assistant for POWERGRID employees. Generate a helpful response to this ticket:

Ticket: "{ticket_text}"
Classification: {json.dumps(classification)}
Language: {language} {"(Mixed Hindi/English)" if is_mixed else ""}
{similar_context}

Guidelines:
1. Respond in the SAME language style as the user (Hindi/English/Mixed)
2. Provide step-by-step solution if possible
3. Be concise but thorough
4. Use POWERGRID-specific context when relevant
5. Include escalation note if issue is complex
6. Be empathetic and professional

If the language is mixed or Hindi, use natural code-switching like POWERGRID employees do.

Generate response with confidence score and indicate if human escalation is recommended.

Response format:
{{
    "response_text": "Your helpful response here...",
    "confidence": 0.0,
    "requires_escalation": true/false,
    "escalation_reason": "Reason if escalation needed",
    "estimated_resolution_time": "Time estimate",
    "follow_up_required": true/false
}}
"""

    def _parse_classification_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's classification response"""
        try:
            # Try to extract JSON from response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start != -1 and end != -1:
                json_str = response_text[start:end]
                return json.loads(json_str)
            else:
                return self._default_classification()
                
        except json.JSONDecodeError:
            logger.error("Failed to parse classification JSON")
            return self._default_classification()
    
    def _parse_response(self, response_text: str, language_info: Dict) -> Dict[str, Any]:
        """Parse Claude's response"""
        try:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start != -1 and end != -1:
                json_str = response_text[start:end]
                parsed = json.loads(json_str)
                parsed["language"] = language_info.get("primary_language", "english")
                return parsed
            else:
                # Fallback: treat entire response as text
                return {
                    "response_text": response_text,
                    "confidence": 0.7,
                    "requires_escalation": False,
                    "escalation_reason": "",
                    "estimated_resolution_time": "1-2 hours",
                    "follow_up_required": False,
                    "language": language_info.get("primary_language", "english")
                }
                
        except json.JSONDecodeError:
            logger.error("Failed to parse response JSON")
            return self._default_response(language_info)
    
    def _default_classification(self) -> Dict[str, Any]:
        """Default classification for errors"""
        return {
            "category": "Other",
            "subcategory": "General",
            "urgency": "medium",
            "confidence": 0.5,
            "reasoning": "Unable to classify automatically",
            "keywords": []
        }
    
    def _default_response(self, language_info: Dict) -> Dict[str, Any]:
        """Default response for errors"""
        is_hindi = language_info.get("primary_language") == "hindi"
        
        default_text = {
            "hindi": "Aapka ticket receive ho gaya hai. Humara technical team jaldi response dega. Kripya thoda wait kariye.",
            "english": "Your ticket has been received. Our technical team will respond shortly. Please wait for further assistance."
        }
        
        return {
            "response_text": default_text.get("hindi" if is_hindi else "english"),
            "confidence": 0.5,
            "requires_escalation": True,
            "escalation_reason": "Unable to generate automated response",
            "estimated_resolution_time": "2-4 hours",
            "follow_up_required": True,
            "language": language_info.get("primary_language", "english")
        }

# Global instance
claude_service = ClaudeAIService()