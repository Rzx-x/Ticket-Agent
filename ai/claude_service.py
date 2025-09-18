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

            # Call model in a robust way and extract text
            model_text = await self._call_model(messages=[{"role": "user", "content": prompt}], max_tokens=1000)

            # Parse Claude's response
            classification = self._parse_classification_response(model_text)
            
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

            model_text = await self._call_model(messages=[{"role": "user", "content": prompt}], max_tokens=1500)

            response_data = self._parse_response(model_text, language_info)
            
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

    async def _call_model(self, messages: List[Dict[str, str]], max_tokens: int = 1000) -> str:
        """Call the configured model/client in a defensive way and return a text response.

        This helper tries several common client shapes (Anthropic/Claude, OpenAI-like) and
        extracts the text content robustly so the rest of the code doesn't rely on a single
        response shape.
        """
        try:
            # Try Anthropic messages.create style first (may be sync)
            try:
                response = await asyncio.to_thread(
                    getattr(self.client, "messages").create,
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=messages
                )
            except Exception:
                # Fallback: try completions / create style
                try:
                    response = await asyncio.to_thread(
                        getattr(self.client, "completions").create,
                        model=self.model,
                        max_tokens=max_tokens,
                        prompt=messages[0]["content"] if messages else ""
                    )
                except Exception:
                    # Last resort: try client.create
                    response = await asyncio.to_thread(
                        getattr(self.client, "create", lambda *a, **k: ""),
                        model=self.model,
                        max_tokens=max_tokens,
                        messages=messages
                    )

            return self._extract_text_from_response(response)
        except Exception as e:
            logger.error(f"Error calling model: {e}")
            return ""

    def _extract_text_from_response(self, response: Any) -> str:
        """Try to extract a readable text string from various possible response shapes."""
        try:
            # If it's already a string
            if isinstance(response, str):
                return response

            # Objects with a 'content' attribute (Anthropic recent SDK)
            if hasattr(response, "content"):
                content = response.content
                if isinstance(content, str):
                    return content
                if isinstance(content, (list, tuple)) and len(content) > 0:
                    first = content[0]
                    if hasattr(first, "text"):
                        return first.text
                    if isinstance(first, dict):
                        return first.get("text") or first.get("content") or str(first)

            # Dict-like shapes (OpenAI style)
            if isinstance(response, dict):
                # OpenAI-like
                choices = response.get("choices")
                if choices and isinstance(choices, list) and len(choices) > 0:
                    first = choices[0]
                    if isinstance(first, dict):
                        # Chat completion
                        if "message" in first and isinstance(first["message"], dict):
                            return first["message"].get("content", "")
                        # Completion
                        return first.get("text", "")

                # Anthropic older style
                if "completion" in response:
                    return response.get("completion")

            # Fallback to string representation
            return str(response)
        except Exception as e:
            logger.error(f"Failed to extract text from model response: {e}")
            return str(response)

# Global instance
claude_service = ClaudeAIService()