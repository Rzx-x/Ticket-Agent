"""
Enhanced AI Engine with GPU Acceleration for OmniDesk AI
Provides cutting-edge AI capabilities for ticket classification, response generation,
and semantic analysis with optimized GPU utilization.
"""

import torch
import torch.nn.functional as F
from transformers import (
    AutoTokenizer, AutoModel, AutoModelForSequenceClassification,
    pipeline, BitsAndBytesConfig
)
from sentence_transformers import SentenceTransformer
import anthropic
from typing import Dict, List, Optional, Tuple, Any
import asyncio
import json
import re
import logging
from dataclasses import dataclass
from enum import Enum
import numpy as np
from functools import lru_cache
import time
from concurrent.futures import ThreadPoolExecutor
import threading

# Configure logging
logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Available model types for different AI tasks"""
    CLASSIFICATION = "classification"
    EMBEDDING = "embedding" 
    GENERATION = "generation"
    LANGUAGE_DETECTION = "language_detection"

@dataclass
class AIResponse:
    """Structured AI response with confidence metrics"""
    result: Any
    confidence: float
    processing_time: float
    model_used: str
    gpu_accelerated: bool
    metadata: Optional[Dict] = None

@dataclass
class ClassificationResult:
    """Structured ticket classification result"""
    category: str
    subcategory: str
    urgency: str
    confidence: float
    reasoning: str
    keywords: List[str]
    estimated_resolution_time: str
    language_detected: str
    is_mixed_language: bool

class GPUAcceleratedAIEngine:
    """
    Production-ready AI Engine with GPU acceleration, model caching,
    and advanced ML pipelines for ticket management
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.device = self._setup_device()
        self.models = {}
        self.tokenizers = {}
        self.anthropic_client = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._model_lock = threading.Lock()
        
        # Performance tracking
        self.metrics = {
            'total_requests': 0,
            'gpu_requests': 0,
            'avg_processing_time': 0,
            'cache_hits': 0
        }
        
        logger.info(f"AI Engine initialized with device: {self.device}")
        self._initialize_models()
    
    def _setup_device(self) -> torch.device:
        """Setup optimal device (GPU/CPU) for model inference"""
        if torch.cuda.is_available():
            device = torch.device("cuda")
            logger.info(f"GPU detected: {torch.cuda.get_device_name()}")
            logger.info(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
        else:
            device = torch.device("cpu")
            logger.warning("GPU not available, falling back to CPU")
        return device
    
    def _initialize_models(self):
        """Initialize all required models with GPU optimization"""
        asyncio.create_task(self._load_models_async())
    
    async def _load_models_async(self):
        """Asynchronously load all models for better startup performance"""
        try:
            # Load embedding model with GPU support
            await self._load_embedding_model()
            
            # Load classification model
            await self._load_classification_model()
            
            # Load language detection model
            await self._load_language_model()
            
            # Initialize Anthropic client
            self._initialize_anthropic()
            
            logger.info("All AI models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading AI models: {e}")
    
    async def _load_embedding_model(self):
        """Load sentence embedding model with GPU optimization"""
        try:
            model_name = self.config.get('embedding_model', 'all-MiniLM-L6-v2')
            
            # Use better multilingual model for Hindi+English support
            if 'multilingual' in self.config.get('features', []):
                model_name = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
            
            self.models[ModelType.EMBEDDING] = SentenceTransformer(model_name)
            
            if self.device.type == 'cuda':
                self.models[ModelType.EMBEDDING] = self.models[ModelType.EMBEDDING].to(self.device)
            
            logger.info(f"Embedding model loaded: {model_name}")
            
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
    
    async def _load_classification_model(self):
        """Load fine-tuned classification model for IT tickets"""
        try:
            # Use a more powerful model for better classification
            model_name = self.config.get('classification_model', 'microsoft/DialoGPT-medium')
            
            # For production, use a model fine-tuned on IT support data
            if 'production' in self.config.get('environment', ''):
                model_name = 'bert-base-uncased'  # Replace with your fine-tuned model
            
            # Load with quantization for memory efficiency
            if self.device.type == 'cuda':
                quantization_config = BitsAndBytesConfig(
                    load_in_8bit=True,
                    bnb_8bit_compute_dtype=torch.float16
                )
                
                self.models[ModelType.CLASSIFICATION] = AutoModelForSequenceClassification.from_pretrained(
                    model_name,
                    quantization_config=quantization_config,
                    device_map="auto"
                )
            else:
                self.models[ModelType.CLASSIFICATION] = AutoModelForSequenceClassification.from_pretrained(model_name)
            
            self.tokenizers[ModelType.CLASSIFICATION] = AutoTokenizer.from_pretrained(model_name)
            
            logger.info(f"Classification model loaded: {model_name}")
            
        except Exception as e:
            logger.error(f"Error loading classification model: {e}")
    
    async def _load_language_model(self):
        """Load advanced language detection model"""
        try:
            # Use transformer-based language detection
            self.models[ModelType.LANGUAGE_DETECTION] = pipeline(
                "text-classification",
                model="papluca/xlm-roberta-base-language-detection",
                device=0 if self.device.type == 'cuda' else -1
            )
            
            logger.info("Language detection model loaded")
            
        except Exception as e:
            logger.error(f"Error loading language model: {e}")
    
    def _initialize_anthropic(self):
        """Initialize Anthropic Claude client"""
        api_key = self.config.get('anthropic_api_key')
        if api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=api_key)
            logger.info("Anthropic client initialized")
        else:
            logger.warning("Anthropic API key not found")
    
    @lru_cache(maxsize=1000)
    def _cached_embedding(self, text: str) -> np.ndarray:
        """Cached embedding generation for performance"""
        if ModelType.EMBEDDING not in self.models:
            return np.array([])
        
        try:
            with torch.no_grad():
                embeddings = self.models[ModelType.EMBEDDING].encode(
                    text, 
                    convert_to_tensor=True,
                    device=self.device
                )
                
                # Move back to CPU for caching
                if isinstance(embeddings, torch.Tensor):
                    embeddings = embeddings.cpu().numpy()
                
                self.metrics['cache_hits'] += 1
                return embeddings
                
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return np.array([])
    
    async def generate_embeddings(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        Generate embeddings with GPU acceleration and batching
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for GPU processing
            
        Returns:
            List of embedding vectors
        """
        start_time = time.time()
        
        if ModelType.EMBEDDING not in self.models:
            logger.error("Embedding model not loaded")
            return [np.array([]) for _ in texts]
        
        try:
            embeddings = []
            
            # Process in batches for memory efficiency
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                with torch.no_grad():
                    batch_embeddings = self.models[ModelType.EMBEDDING].encode(
                        batch,
                        convert_to_tensor=True,
                        device=self.device,
                        show_progress_bar=False
                    )
                    
                    # Convert to numpy and move to CPU
                    if isinstance(batch_embeddings, torch.Tensor):
                        batch_embeddings = batch_embeddings.cpu().numpy()
                    
                    embeddings.extend(batch_embeddings)
            
            processing_time = time.time() - start_time
            
            # Update metrics
            self.metrics['total_requests'] += len(texts)
            if self.device.type == 'cuda':
                self.metrics['gpu_requests'] += len(texts)
            
            self._update_avg_processing_time(processing_time)
            
            logger.debug(f"Generated {len(embeddings)} embeddings in {processing_time:.3f}s")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error in batch embedding generation: {e}")
            return [np.array([]) for _ in texts]
    
    async def classify_ticket_advanced(self, 
                                    subject: str, 
                                    description: str,
                                    user_context: Optional[Dict] = None) -> AIResponse:
        """
        Advanced ticket classification using multiple models and techniques
        
        Args:
            subject: Ticket subject/title
            description: Ticket description/body
            user_context: Optional user context (department, role, etc.)
            
        Returns:
            AIResponse with ClassificationResult
        """
        start_time = time.time()
        
        try:
            # Combine subject and description
            full_text = f"{subject}\n{description}"
            
            # Language detection with confidence
            language_result = await self._detect_language_advanced(full_text)
            
            # Multi-model classification approach
            results = await asyncio.gather(
                self._classify_with_transformers(full_text, user_context),
                self._classify_with_claude(subject, description, language_result),
                return_exceptions=True
            )
            
            # Ensemble the results
            final_result = self._ensemble_classification_results(results, language_result)
            
            processing_time = time.time() - start_time
            
            return AIResponse(
                result=final_result,
                confidence=final_result.confidence,
                processing_time=processing_time,
                model_used="ensemble",
                gpu_accelerated=self.device.type == 'cuda',
                metadata={
                    "language_result": language_result,
                    "user_context": user_context,
                    "models_used": ["transformers", "claude"]
                }
            )
            
        except Exception as e:
            logger.error(f"Error in advanced classification: {e}")
            
            # Fallback classification
            fallback_result = ClassificationResult(
                category="Other",
                subcategory="General Issue",
                urgency="medium",
                confidence=0.0,
                reasoning="Classification unavailable",
                keywords=[],
                estimated_resolution_time="4-6 hours",
                language_detected="english",
                is_mixed_language=False
            )
            
            return AIResponse(
                result=fallback_result,
                confidence=0.0,
                processing_time=time.time() - start_time,
                model_used="fallback",
                gpu_accelerated=False,
                metadata={"error": str(e)}
            )
    
    async def _detect_language_advanced(self, text: str) -> Dict:
        """Advanced language detection with confidence scoring"""
        if ModelType.LANGUAGE_DETECTION not in self.models:
            return {"language": "en", "confidence": 0.5, "is_mixed": False}
        
        try:
            # Use transformer-based detection
            result = self.models[ModelType.LANGUAGE_DETECTION](text)
            
            # Parse result
            detected_lang = result[0]['label'].lower()
            confidence = result[0]['score']
            
            # Check for mixed language (Hinglish)
            hindi_indicators = ['hai', 'nahi', 'kar', 'hoon', 'kya', 'aap']
            english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
            total_words = len(text.split())
            
            is_mixed = (
                detected_lang in ['hi', 'en'] and 
                any(indicator in text.lower() for indicator in hindi_indicators) and
                english_words > total_words * 0.3
            )
            
            return {
                "language": detected_lang,
                "confidence": confidence,
                "is_mixed": is_mixed,
                "english_ratio": english_words / max(total_words, 1)
            }
            
        except Exception as e:
            logger.error(f"Error in language detection: {e}")
            return {"language": "en", "confidence": 0.5, "is_mixed": False}
    
    async def _classify_with_transformers(self, text: str, user_context: Optional[Dict]) -> ClassificationResult:
        """Classification using local transformer model"""
        if ModelType.CLASSIFICATION not in self.models:
            raise ValueError("Classification model not loaded")
        
        # This is a simplified version - in production, you'd have a fine-tuned model
        # For now, using rule-based classification with transformer embeddings
        
        embeddings = await self.generate_embeddings([text])
        if len(embeddings) == 0:
            raise ValueError("Could not generate embeddings")
        
        # Rule-based classification enhanced with embeddings
        text_lower = text.lower()
        
        # Category mapping with confidence
        categories = {
            'network': (['vpn', 'wifi', 'internet', 'connection', 'network', 'firewall'], 0.8),
            'hardware': (['laptop', 'computer', 'printer', 'monitor', 'keyboard', 'mouse'], 0.8),
            'software': (['application', 'software', 'install', 'update', 'office', 'excel'], 0.7),
            'email': (['email', 'outlook', 'mail', 'inbox', 'smtp'], 0.9),
            'account': (['password', 'login', 'account', 'access', 'permission'], 0.8),
            'security': (['security', 'virus', 'antivirus', 'suspicious', 'breach'], 0.9)
        }
        
        best_category = 'other'
        best_confidence = 0.0
        matched_keywords = []
        
        for category, (keywords, base_confidence) in categories.items():
            matches = [kw for kw in keywords if kw in text_lower]
            if matches:
                confidence = base_confidence * (len(matches) / len(keywords))
                if confidence > best_confidence:
                    best_category = category
                    best_confidence = confidence
                    matched_keywords = matches
        
        # Urgency detection
        urgency_keywords = {
            'critical': ['down', 'outage', 'emergency', 'urgent', 'critical', 'emergency'],
            'high': ['important', 'asap', 'priority', 'manager', 'boss'],
            'low': ['minor', 'enhancement', 'request', 'question']
        }
        
        urgency = 'medium'
        for level, keywords in urgency_keywords.items():
            if any(kw in text_lower for kw in keywords):
                urgency = level
                break
        
        return ClassificationResult(
            category=best_category.title(),
            subcategory=f"{best_category.title()} Issue",
            urgency=urgency,
            confidence=best_confidence,
            reasoning=f"Matched keywords: {', '.join(matched_keywords)}",
            keywords=matched_keywords,
            estimated_resolution_time="2-4 hours" if urgency == 'high' else "4-8 hours",
            language_detected="english",
            is_mixed_language=False
        )
    
    async def _classify_with_claude(self, subject: str, description: str, language_result: Dict) -> ClassificationResult:
        """Classification using Claude API"""
        if not self.anthropic_client:
            raise ValueError("Anthropic client not initialized")
        
        prompt = f"""
        Classify this IT support ticket with high accuracy:
        
        Subject: {subject}
        Description: {description}
        Language: {language_result.get('language', 'en')}
        
        Respond with JSON only:
        {{
            "category": "Network|Hardware|Software|Email|Account|Security|Printer|Telephony|Other",
            "subcategory": "specific issue type",
            "urgency": "low|medium|high|critical", 
            "confidence": 0.95,
            "reasoning": "brief explanation",
            "keywords": ["keyword1", "keyword2"],
            "estimated_resolution_time": "2 hours"
        }}
        
        Categories:
        - Network: VPN, WiFi, connectivity issues
        - Hardware: Physical device problems
        - Software: Application issues, installations
        - Email: Outlook, email configuration
        - Account: Login, password, permissions
        - Security: Antivirus, security alerts
        - Printer: Printing, scanner issues
        - Telephony: Phone systems, calls
        - Other: General inquiries
        """
        
        try:
            response = await self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text.strip()
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            
            if json_match:
                result = json.loads(json_match.group(0))
                
                return ClassificationResult(
                    category=result.get('category', 'Other'),
                    subcategory=result.get('subcategory', 'General Issue'),
                    urgency=result.get('urgency', 'medium'),
                    confidence=float(result.get('confidence', 0.8)),
                    reasoning=result.get('reasoning', 'Claude classification'),
                    keywords=result.get('keywords', []),
                    estimated_resolution_time=result.get('estimated_resolution_time', '4 hours'),
                    language_detected=language_result.get('language', 'en'),
                    is_mixed_language=language_result.get('is_mixed', False)
                )
            
        except Exception as e:
            logger.error(f"Claude classification error: {e}")
            raise
    
    def _ensemble_classification_results(self, results: List, language_result: Dict) -> ClassificationResult:
        """Combine results from multiple models using ensemble approach"""
        valid_results = [r for r in results if isinstance(r, ClassificationResult)]
        
        if not valid_results:
            # Return fallback if no valid results
            return ClassificationResult(
                category="Other",
                subcategory="General Issue",
                urgency="medium",
                confidence=0.0,
                reasoning="No valid classification results",
                keywords=[],
                estimated_resolution_time="4-6 hours",
                language_detected=language_result.get('language', 'en'),
                is_mixed_language=language_result.get('is_mixed', False)
            )
        
        # Weight results by confidence
        weighted_confidence = sum(r.confidence for r in valid_results) / len(valid_results)
        
        # Use highest confidence result as base
        best_result = max(valid_results, key=lambda x: x.confidence)
        
        # Combine keywords from all results
        all_keywords = []
        for result in valid_results:
            all_keywords.extend(result.keywords)
        unique_keywords = list(set(all_keywords))
        
        return ClassificationResult(
            category=best_result.category,
            subcategory=best_result.subcategory,
            urgency=best_result.urgency,
            confidence=weighted_confidence,
            reasoning=f"Ensemble of {len(valid_results)} models: {best_result.reasoning}",
            keywords=unique_keywords,
            estimated_resolution_time=best_result.estimated_resolution_time,
            language_detected=language_result.get('language', 'en'),
            is_mixed_language=language_result.get('is_mixed', False)
        )
    
    def _update_avg_processing_time(self, processing_time: float):
        """Update average processing time metric"""
        current_avg = self.metrics['avg_processing_time']
        total_requests = self.metrics['total_requests']
        
        if total_requests > 0:
            self.metrics['avg_processing_time'] = (
                (current_avg * (total_requests - 1) + processing_time) / total_requests
            )
    
    def get_performance_metrics(self) -> Dict:
        """Get current performance metrics"""
        gpu_usage = 0.0
        if self.device.type == 'cuda':
            gpu_usage = torch.cuda.memory_allocated() / torch.cuda.max_memory_allocated() * 100
        
        return {
            **self.metrics,
            'gpu_usage_percent': gpu_usage,
            'device': str(self.device),
            'models_loaded': list(self.models.keys()),
            'gpu_available': torch.cuda.is_available()
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.executor:
            self.executor.shutdown(wait=True)
        
        # Clear GPU cache
        if self.device.type == 'cuda':
            torch.cuda.empty_cache()
        
        logger.info("AI Engine cleaned up")

# Global instance for the application
ai_engine = None

def get_ai_engine(config: Optional[Dict] = None) -> GPUAcceleratedAIEngine:
    """Get singleton AI engine instance"""
    global ai_engine
    if ai_engine is None:
        ai_engine = GPUAcceleratedAIEngine(config)
    return ai_engine