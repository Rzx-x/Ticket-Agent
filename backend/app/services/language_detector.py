import re
import string
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class LanguageDetector:
    def __init__(self):
        # Hindi Unicode ranges
        self.hindi_chars = set(range(0x0900, 0x097F))  # Devanagari
        # English characters, numbers, and common symbols
        self.english_and_symbols_chars = set(string.ascii_letters + string.digits + string.punctuation)
        
        # Common Hindi words in Roman script
        self.hinglish_patterns = {
            'nahi', 'hai', 'hoon', 'kya', 'kaise', 'kyun', 'kar', 'karo', 
            'chal', 'raha', 'gaya', 'diya', 'liya', 'acha', 'bhi', 'main',
            'aap', 'hum', 'yeh', 'woh', 'kuch', 'sab', 'problem', 'issue',
            'working', 'nai', 'ho', 'ja', 'le', 'de', 'pe', 'me', 'se'
        }
    
    def detect_language(self, text: str) -> Dict[str, any]:
        """
        Detect language and return detailed analysis
        Returns: {
            'primary_language': str,
            'is_mixed': bool,
            'confidence': float,
            'hindi_ratio': float,
            'english_ratio': float
        }
        """
        try:
            if not text.strip():
                return self._default_result()
            
            # Clean and normalize text
            cleaned_text = self._clean_text(text)
            
            # Character-level analysis
            char_analysis = self._analyze_characters(cleaned_text)
            
            # Word-level analysis
            word_analysis = self._analyze_words(cleaned_text)
            
            # Combined analysis
            result = self._combine_analysis(char_analysis, word_analysis)
            
            logger.info(f"Language detection result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in language detection: {e}")
            return self._default_result()
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for analysis"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        # Allow numbers, common punctuation, and Hindi Unicode characters
        text = re.sub(r'[^\w\s\u0900-\u097F\.,!?"\'\-]', '', text)
        return text.lower()
    
    def _analyze_characters(self, text: str) -> Dict[str, float]:
        """Analyze characters to determine script usage"""
        total_chars = 0
        hindi_chars = 0
        english_chars = 0
        
        for char in text:
            if char.isalpha():
                total_chars += 1
                char_code = ord(char)
                
                if char_code in self.hindi_chars:
                    hindi_chars += 1
                elif char in self.english_and_symbols_chars:
                    english_chars += 1
        
        if total_chars == 0:
            return {"hindi_ratio": 0.0, "english_ratio": 0.0}
        
        return {
            "hindi_ratio": hindi_chars / total_chars,
            "english_ratio": english_chars / total_chars
        }
    
    def _analyze_words(self, text: str) -> Dict[str, float]:
        """Analyze words for Hinglish patterns"""
        words = text.split()
        total_words = len(words)
        hinglish_words = 0
        
        if total_words == 0:
            return {"hinglish_ratio": 0.0}
        
        for word in words:
            # Remove punctuation
            clean_word = word.strip('.,!?')
            if clean_word.lower() in self.hinglish_patterns:
                hinglish_words += 1
        
        return {"hinglish_ratio": hinglish_words / total_words}
    
    def _combine_analysis(self, char_analysis: Dict, word_analysis: Dict) -> Dict:
        """Combine character and word analysis"""
        hindi_ratio = char_analysis.get("hindi_ratio", 0)
        english_ratio = char_analysis.get("english_ratio", 0)
        hinglish_ratio = word_analysis.get("hinglish_ratio", 0)
        
        # Adjust ratios based on Hinglish detection
        # A higher hinglish ratio suggests more Hindi influence, so boost hindi_ratio
        if hinglish_ratio > 0.1:
            hindi_ratio += hinglish_ratio * 0.3  # Moderate boost for Hindi if Hinglish is present
        
        # Normalize ratios to sum to 1 if they exceed it due to boosting
        total_script_ratio = hindi_ratio + english_ratio
        if total_script_ratio > 1.0:
            hindi_ratio /= total_script_ratio
            english_ratio /= total_script_ratio

        # Determine primary language with more balanced thresholds
        if hindi_ratio > 0.45: # If Hindi script is dominant
            primary_language = "hindi"
        elif english_ratio > 0.6: # If English script is dominant
            primary_language = "english"
        elif hinglish_ratio > 0.15: # If significant Hinglish words, lean towards mixed
            primary_language = "mixed"
        else:
            primary_language = "english" # Default to English if no strong indicators

        # Check if mixed: significant presence of both scripts or notable Hinglish
        is_mixed = (hindi_ratio > 0.15 and english_ratio > 0.15) or hinglish_ratio > 0.15
        
        # Calculate confidence based on the primary language's dominance
        if primary_language == "hindi":
            confidence = hindi_ratio
        elif primary_language == "english":
            confidence = english_ratio
        else: # mixed
            confidence = max(hindi_ratio, english_ratio) * 0.7 + hinglish_ratio * 0.3 # Weighted for mixed
        
        # Ensure confidence is within 0-1 range
        confidence = min(1.0, max(0.0, confidence))

        return {
            "primary_language": primary_language,
            "is_mixed": is_mixed,
            "confidence": confidence,
            "hindi_ratio": hindi_ratio,
            "english_ratio": english_ratio,
            "hinglish_ratio": hinglish_ratio
        }
    
    def _default_result(self) -> Dict:
        """Default result for errors or empty text"""
        return {
            "primary_language": "english",
            "is_mixed": False,
            "confidence": 0.5,
            "hindi_ratio": 0.0,
            "english_ratio": 1.0,
            "hinglish_ratio": 0.0
        }

# Global instance
language_detector = LanguageDetector()
