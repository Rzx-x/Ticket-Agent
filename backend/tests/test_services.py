import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.ai_service import AIService
from app.services.vector_service import VectorSearchService
from app.services.language_detector import LanguageDetector
from app.core.config import settings

class TestAIService:
    \"\"\"Test AI service functionality\"\"\"
    
    @pytest.fixture
    def ai_service(self):
        \"\"\"Create AI service instance for testing\"\"\"
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = \"test-key\"
            service = AIService()
            return service
    
    def test_ai_service_initialization(self):
        \"\"\"Test AI service initialization\"\"\"
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = \"test-key\"
            service = AIService()
            assert service.is_available() == True
    
    def test_ai_service_no_api_key(self):
        \"\"\"Test AI service without API key\"\"\"
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = None
            service = AIService()
            assert service.is_available() == False
    
    def test_language_detection(self, ai_service):
        \"\"\"Test language detection functionality\"\"\"
        # English text
        result = ai_service.detect_language(\"This is an English sentence.\")
        assert isinstance(result, str)
        
        # Hindi mixed text
        result = ai_service.detect_language(\"Mera computer nahi chal raha hai please help\")
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_classify_ticket_fallback(self, ai_service):
        \"\"\"Test ticket classification fallback\"\"\"
        # Mock AI service as unavailable
        ai_service.client = None
        
        result = await ai_service.classify_ticket(
            \"VPN Issues\", 
            \"Cannot connect to VPN\"
        )
        
        assert result[\"category\"] == \"Other\"
        assert result[\"urgency\"] == \"medium\"
        assert result[\"confidence\"] == 0.0
    
    @pytest.mark.asyncio
    async def test_classify_ticket_success(self, ai_service):
        \"\"\"Test successful ticket classification\"\"\"
        # Mock the Anthropic client
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = '''{
            \"category\": \"Network\",
            \"subcategory\": \"VPN Issues\",
            \"urgency\": \"high\",
            \"confidence\": 0.95,
            \"reasoning\": \"VPN connection problem\"
        }'''
        
        with patch.object(ai_service.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            result = await ai_service.classify_ticket(
                \"VPN Connection Issues\",
                \"Cannot connect to company VPN\"
            )
            
            assert result[\"category\"] == \"Network\"
            assert result[\"urgency\"] == \"high\"
            assert result[\"confidence\"] == 0.95
    
    @pytest.mark.asyncio
    async def test_generate_response_fallback(self, ai_service):
        \"\"\"Test AI response generation fallback\"\"\"
        # Mock AI service as unavailable
        ai_service.client = None
        
        result = await ai_service.generate_response(
            \"Test Subject\",
            \"Test Description\",
            \"en\",
            \"Network\",
            \"Test User\"
        )
        
        assert \"Thank you for contacting\" in result or \"POWERGRID IT Support\" in result
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, ai_service):
        \"\"\"Test successful AI response generation\"\"\"
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = \"I understand your VPN issue. Please try these steps...\"
        
        with patch.object(ai_service.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            result = await ai_service.generate_response(
                \"VPN Issues\",
                \"Cannot connect\", 
                \"en\",
                \"Network\",
                \"John Doe\"
            )
            
            assert \"VPN issue\" in result

class TestVectorService:
    \"\"\"Test vector search service functionality\"\"\"
    
    @pytest.fixture
    def vector_service(self):
        \"\"\"Create vector service instance for testing\"\"\"
        with patch('app.services.vector_service.QdrantClient'), \\n             patch('app.services.vector_service.SentenceTransformer'):
            service = VectorSearchService()
            service._initialized = True
            service._client = MagicMock()
            service._embedding_model = MagicMock()
            return service
    
    def test_vector_service_availability(self, vector_service):
        \"\"\"Test vector service availability check\"\"\"
        assert vector_service.is_available() == True
        
        # Test unavailable service
        vector_service._initialized = False
        assert vector_service.is_available() == False
    
    def test_generate_embeddings(self, vector_service):
        \"\"\"Test embedding generation\"\"\"
        # Mock embedding model
        vector_service._embedding_model.encode.return_value = [0.1, 0.2, 0.3]
        
        result = vector_service.generate_embeddings(\"Test text\")
        assert result == [0.1, 0.2, 0.3]
    
    def test_generate_embeddings_empty_text(self, vector_service):
        \"\"\"Test embedding generation with empty text\"\"\"
        result = vector_service.generate_embeddings(\"\")
        assert result == []
        
        result = vector_service.generate_embeddings(\"   \")
        assert result == []
    
    @pytest.mark.asyncio
    async def test_add_ticket_vector(self, vector_service):
        \"\"\"Test adding ticket to vector database\"\"\"
        vector_service._embedding_model.encode.return_value = [0.1, 0.2, 0.3]
        vector_service._client.upsert.return_value = None
        
        result = await vector_service.add_ticket_vector(
            \"ticket-123\",
            \"VPN connection issues\",
            {\"category\": \"Network\", \"urgency\": \"high\"}
        )
        
        assert result == True
        vector_service._client.upsert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_similar_tickets(self, vector_service):
        \"\"\"Test searching for similar tickets\"\"\"
        vector_service._embedding_model.encode.return_value = [0.1, 0.2, 0.3]
        
        # Mock search results
        mock_result = MagicMock()
        mock_result.id = \"ticket-456\"
        mock_result.score = 0.89
        mock_result.payload = {\"category\": \"Network\"}
        
        vector_service._client.search.return_value = [mock_result]
        
        results = await vector_service.search_similar_tickets(
            \"VPN problems\",
            limit=5
        )
        
        assert len(results) == 1
        assert results[0][\"ticket_id\"] == \"ticket-456\"
        assert results[0][\"similarity_score\"] == 0.89
    
    @pytest.mark.asyncio
    async def test_search_knowledge_base(self, vector_service):
        \"\"\"Test knowledge base search\"\"\"
        vector_service._embedding_model.encode.return_value = [0.1, 0.2, 0.3]
        
        # Mock search results
        mock_result = MagicMock()
        mock_result.id = \"article-123\"
        mock_result.score = 0.92
        mock_result.payload = {\"title\": \"VPN Troubleshooting\"}
        
        vector_service._client.search.return_value = [mock_result]
        
        results = await vector_service.search_knowledge_base(
            \"VPN setup\",
            limit=3
        )
        
        assert len(results) == 1
        assert results[0][\"article_id\"] == \"article-123\"
        assert results[0][\"relevance_score\"] == 0.92

class TestLanguageDetector:
    \"\"\"Test language detection functionality\"\"\"
    
    @pytest.fixture
    def language_detector(self):
        \"\"\"Create language detector instance\"\"\"
        return LanguageDetector()
    
    def test_detect_english(self, language_detector):
        \"\"\"Test English language detection\"\"\"
        result = language_detector.detect_language(
            \"This is a simple English sentence for testing.\"
        )
        
        assert \"primary_language\" in result
        assert \"confidence\" in result
        assert \"languages_detected\" in result
    
    def test_detect_hindi_mixed(self, language_detector):
        \"\"\"Test Hindi-English mixed language detection\"\"\"
        result = language_detector.detect_language(
            \"Mera computer nahi chal raha hai, please help me\"
        )
        
        assert \"primary_language\" in result
        assert \"confidence\" in result
        assert \"languages_detected\" in result
    
    def test_detect_empty_text(self, language_detector):
        \"\"\"Test language detection with empty text\"\"\"
        result = language_detector.detect_language(\"\")
        
        assert result[\"primary_language\"] == \"en\"  # Default to English
        assert result[\"confidence\"] == 0.0
    
    def test_detect_short_text(self, language_detector):
        \"\"\"Test language detection with very short text\"\"\"
        result = language_detector.detect_language(\"Hi\")
        
        assert \"primary_language\" in result
        assert isinstance(result[\"confidence\"], (int, float))

class TestServiceIntegration:
    \"\"\"Test integration between services\"\"\"
    
    @pytest.mark.asyncio
    async def test_ai_with_language_detection(self):
        \"\"\"Test AI service with language detection\"\"\"
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = \"test-key\"
            
            ai_service = AIService()
            
            # Mock language detector
            with patch.object(ai_service.language_detector, 'detect_language') as mock_detect:
                mock_detect.return_value = {
                    \"primary_language\": \"hi\",
                    \"confidence\": 0.8,
                    \"languages_detected\": [\"hi\", \"en\"]
                }
                
                # Test detect_language method
                result = ai_service.detect_language(\"Test text\")
                assert result == \"hi\"
    
    @pytest.mark.asyncio
    async def test_vector_service_error_handling(self):
        \"\"\"Test vector service error handling\"\"\"
        with patch('app.services.vector_service.QdrantClient'), \\n             patch('app.services.vector_service.SentenceTransformer'):
            
            service = VectorSearchService()
            service._initialized = True
            service._client = MagicMock()
            service._embedding_model = MagicMock()
            
            # Test embedding generation failure
            service._embedding_model.encode.side_effect = Exception(\"Model error\")
            
            result = service.generate_embeddings(\"Test text\")
            assert result == []
            
            # Test search failure
            service._embedding_model.encode.side_effect = None
            service._embedding_model.encode.return_value = [0.1, 0.2, 0.3]
            service._client.search.side_effect = Exception(\"Search error\")
            
            results = await service.search_similar_tickets(\"Test query\")
            assert results == []

if __name__ == \"__main__\":
    pytest.main([\"-v\", __file__])