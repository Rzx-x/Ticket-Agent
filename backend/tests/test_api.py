#!/usr/bin/env python3
"""
Test script for OmniDesk AI Backend API
Run this after starting the server to verify all endpoints work correctly
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_response(title, response):
    print(f"\n{'='*50}")
    print(f"🧪 {title}")
    print(f"{'='*50}")
    print(f"Status Code: {response.status_code}")
    
    try:
        json_response = response.json()
        print(f"Response: {json.dumps(json_response, indent=2, default=str)}")
    except:
        print(f"Response: {response.text}")
    
    print(f"{'='*50}\n")

def test_health_endpoints():
    """Test health and info endpoints"""
    print("🏥 Testing Health Endpoints...")
    
    # Root endpoint
    response = requests.get(f"{BASE_URL}/")
    print_response("Root Endpoint", response)
    
    # Health check
    response = requests.get(f"{BASE_URL}/health")
    print_response("Health Check", response)
    
    # System info
    response = requests.get(f"{BASE_URL}/api/v1/system/info")
    print_response("System Info", response)

def test_ticket_creation():
    """Test ticket creation with different scenarios"""
    print("🎫 Testing Ticket Creation...")
    
    # Test 1: Basic English ticket
    ticket_data = {
        "source": "web",
        "user_email": "john.doe@powergrid.in",
        "user_name": "John Doe",
        "subject": "VPN Connection Issues",
        "description": "I am unable to connect to the company VPN. Getting error message 'Connection failed to establish'.",
        "urgency": "high"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/tickets/", json=ticket_data)
    print_response("Create English VPN Ticket", response)
    
    if response.status_code == 200:
        global test_ticket_id
        test_ticket_id = response.json()["id"]
    
    # Test 2: Hindi mixed ticket
    ticket_data_hindi = {
        "source": "email",
        "user_email": "priya.sharma@powergrid.in", 
        "user_name": "Priya Sharma",
        "subject": "Printer problem hai",
        "description": "Mere desktop se printer connect nahi ho raha. Network printer HP LaserJet main kya problem hai? Please help karo.",
        "urgency": "medium"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/tickets/", json=ticket_data_hindi)
    print_response("Create Hindi/English Mixed Ticket", response)
    
    # Test 3: Critical hardware issue
    ticket_data_critical = {
        "source": "phone",
        "user_email": "manager@powergrid.in",
        "user_name": "IT Manager", 
        "user_phone": "+91-9876543210",
        "subject": "Server Down - Production Impact",
        "description": "Main production server is completely down. All applications are inaccessible. Immediate attention required.",
        "urgency": "critical"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/tickets/", json=ticket_data_critical)
    print_response("Create Critical Server Ticket", response)
    
    return test_ticket_id if 'test_ticket_id' in globals() else None

def test_ticket_operations(ticket_id):
    """Test ticket retrieval and updates"""
    if not ticket_id:
        print("❌ No ticket ID available for testing operations")
        return
    
    print("🔄 Testing Ticket Operations...")
    
    # Get specific ticket
    response = requests.get(f"{BASE_URL}/api/v1/tickets/{ticket_id}")
    print_response("Get Specific Ticket", response)
    
    # Update ticket status
    update_data = {
        "status": "in_progress",
        "assigned_to": "IT Support Agent",
        "resolution_notes": "Working on VPN configuration..."
    }
    
    response = requests.put(f"{BASE_URL}/api/v1/tickets/{ticket_id}", json=update_data)
    print_response("Update Ticket Status", response)
    
    # Add interaction
    interaction_data = {
        "interaction_type": "agent_response",
        "content": "I've identified the VPN issue. Please try reconnecting now.",
        "sender": "IT Support Agent"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/tickets/{ticket_id}/interactions", json=interaction_data)
    print_response("Add Agent Interaction", response)
    
    # Regenerate AI response
    response = requests.post(f"{BASE_URL}/api/v1/tickets/{ticket_id}/regenerate-ai-response")
    print_response("Regenerate AI Response", response)

def test_search_and_analytics():
    """Test search and analytics features"""
    print("🔍 Testing Search and Analytics...")
    
    # Get all tickets
    response = requests.get(f"{BASE_URL}/api/v1/tickets/")
    print_response("Get All Tickets", response)
    
    #  Search tickets
    search_data = {
    "query": "VPN",
    "filters": {
        "urgency": "high"
    }
}

response = requests.post(f"{BASE_URL}/api/v1/tickets/search", json=search_data)
print_response("Search Tickets", response)
