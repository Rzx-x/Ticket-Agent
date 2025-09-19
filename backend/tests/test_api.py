import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings
import os
from typing import Generator
from unittest.mock import patch, MagicMock

# Test database URL - use SQLite for tests
TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Override database dependency for tests
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def test_db():
    """Create test database tables"""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    # Clean up test database file
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest.fixture
def client(test_db) -> Generator:
    """Create test client"""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def mock_ai_service():
    """Mock AI service for testing"""
    with patch('app.services.ai_service.ai_service') as mock:
        mock.is_available.return_value = True
        mock.classify_ticket.return_value = {
            "category": "Network",
            "subcategory": "VPN Issues", 
            "urgency": "high",
            "confidence": 0.95,
            "reasoning": "VPN connection issue"
        }
        mock.generate_response.return_value = "Please try restarting your VPN client and reconnecting."
        mock.detect_language.return_value = "en"
        yield mock

@pytest.fixture
def mock_vector_service():
    """Mock vector service for testing"""
    with patch('app.services.vector_service.vector_service') as mock:
        mock.is_available.return_value = True
        mock.search_similar_tickets.return_value = [
            {
                "ticket_id": "test-123",
                "similarity_score": 0.89,
                "metadata": {"category": "Network"}
            }
        ]
        yield mock

class TestHealthEndpoints:
    """Test health and system endpoints"""
    
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
    
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data
        assert "database" in data["services"]
    
    def test_system_info(self, client):
        response = client.get("/api/v1/system/info")
        assert response.status_code == 200
        data = response.json()
        assert "app_name" in data
        assert "features" in data
        assert "supported_sources" in data

class TestTicketCreation:
    """Test ticket creation with various scenarios"""
    
    def test_create_basic_ticket(self, client, mock_ai_service):
        ticket_data = {
            "source": "web",
            "user_email": "test@powergrid.com",
            "user_name": "Test User",
            "subject": "Test Subject",
            "description": "Test description",
            "urgency": "medium"
        }
        
        response = client.post("/api/v1/tickets/", json=ticket_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "ticket_number" in data
        assert data["subject"] == ticket_data["subject"]
        assert data["user_email"] == ticket_data["user_email"]
    
    def test_create_ticket_missing_required_fields(self, client):
        ticket_data = {
            "source": "web",
            # Missing required fields
        }
        
        response = client.post("/api/v1/tickets/", json=ticket_data)
        assert response.status_code == 422  # Validation error
    
    def test_create_ticket_invalid_email(self, client):
        ticket_data = {
            "source": "web",
            "user_email": "invalid-email",
            "subject": "Test",
            "description": "Test description"
        }
        
        response = client.post("/api/v1/tickets/", json=ticket_data)
        assert response.status_code == 422
    
    def test_create_hindi_ticket(self, client, mock_ai_service):
        ticket_data = {
            "source": "email",
            "user_email": "priya@powergrid.com",
            "user_name": "Priya Sharma",
            "subject": "Email problem hai",
            "description": "Mera email nahi aa raha, please help karo",
            "urgency": "high"
        }
        
        response = client.post("/api/v1/tickets/", json=ticket_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["subject"] == ticket_data["subject"]

class TestTicketOperations:
    """Test ticket retrieval and updates"""
    
    @pytest.fixture
    def sample_ticket(self, client, mock_ai_service):
        """Create a sample ticket for testing"""
        ticket_data = {
            "source": "web",
            "user_email": "test@powergrid.com",
            "user_name": "Test User",
            "subject": "Sample Ticket",
            "description": "Sample description",
            "urgency": "medium"
        }
        
        response = client.post("/api/v1/tickets/", json=ticket_data)
        return response.json()
    
    def test_get_ticket_by_id(self, client, sample_ticket):
        ticket_id = sample_ticket["id"]
        
        response = client.get(f"/api/v1/tickets/{ticket_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == ticket_id
    
    def test_get_nonexistent_ticket(self, client):
        response = client.get("/api/v1/tickets/nonexistent-id")
        assert response.status_code == 404
    
    def test_update_ticket(self, client, sample_ticket):
        ticket_id = sample_ticket["id"]
        
        update_data = {
            "status": "in_progress",
            "assigned_to": "IT Agent"
        }
        
        response = client.put(f"/api/v1/tickets/{ticket_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "in_progress"
        assert data["assigned_to"] == "IT Agent"
    
    def test_add_interaction(self, client, sample_ticket):
        ticket_id = sample_ticket["id"]
        
        interaction_data = {
            "interaction_type": "agent_response",
            "content": "I'm working on your issue",
            "sender": "IT Agent"
        }
        
        response = client.post(f"/api/v1/tickets/{ticket_id}/interactions", json=interaction_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["content"] == interaction_data["content"]
    
    def test_regenerate_ai_response(self, client, sample_ticket, mock_ai_service):
        ticket_id = sample_ticket["id"]
        
        response = client.post(f"/api/v1/tickets/{ticket_id}/regenerate-ai-response")
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data

class TestTicketSearch:
    """Test ticket search and filtering"""
    
    def test_get_all_tickets(self, client):
        response = client.get("/api/v1/tickets/")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_filter_tickets_by_status(self, client):
        response = client.get("/api/v1/tickets/?status=open")
        assert response.status_code == 200
    
    def test_search_tickets(self, client, mock_vector_service):
        search_data = {
            "query": "VPN issues",
            "limit": 5
        }
        
        response = client.post("/api/v1/tickets/search", json=search_data)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_similar_tickets(self, client, sample_ticket, mock_vector_service):
        ticket_id = sample_ticket["id"]
        
        response = client.get(f"/api/v1/tickets/{ticket_id}/similar")
        assert response.status_code == 200
        
        data = response.json()
        assert "similar_tickets" in data

class TestAnalytics:
    """Test analytics endpoints"""
    
    def test_analytics_dashboard(self, client):
        response = client.get("/api/v1/tickets/analytics/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_tickets" in data
        assert "tickets_by_category" in data
        assert "tickets_by_urgency" in data

class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_invalid_json_body(self, client):
        response = client.post(
            "/api/v1/tickets/",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_content_type(self, client):
        response = client.post("/api/v1/tickets/", data="{}")
        # Should still work with FastAPI's automatic content type detection
        assert response.status_code in [422, 400]

class TestFileUpload:
    """Test file upload functionality"""
    
    def test_upload_attachment(self, client, sample_ticket):
        ticket_id = sample_ticket["id"]
        
        # Create a test file
        test_file_content = b"This is a test file"
        files = {"file": ("test.txt", test_file_content, "text/plain")}
        
        response = client.post(f"/api/v1/tickets/{ticket_id}/upload", files=files)
        assert response.status_code == 200
        
        data = response.json()
        assert "attachment_id" in data
        assert "filename" in data

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main(["-v", __file__])
