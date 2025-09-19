#!/usr/bin/env python3
"""
Simple FastAPI application for OmniDesk AI - Initial deployment version
This is a minimal version to get the deployment working, then we can gradually add features.
"""

import os
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="OmniDesk AI - Simple Version",
    description="Smart IT Ticket Management System - Initial Deployment",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "OmniDesk AI is running!",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "services": {
            "api": "healthy",
            "database": "not_connected",  # Will implement later
            "ai": "not_configured",       # Will implement later
            "vector_search": "not_configured"  # Will implement later
        }
    }

@app.get("/api/v1/system/info")
async def system_info():
    """System information endpoint"""
    return {
        "app_name": "OmniDesk AI",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "features": {
            "ai_classification": False,  # Will enable later
            "vector_search": False,      # Will enable later
            "multi_language": False,     # Will enable later
            "email_integration": False,  # Will enable later
            "sms_integration": False,    # Will enable later
            "analytics_dashboard": False # Will enable later
        },
        "supported_sources": ["web"],  # Will add more later
        "supported_languages": ["en"]   # Will add more later
    }

# Simple ticket endpoints (placeholder)
@app.get("/api/v1/tickets")
async def list_tickets():
    """List tickets - placeholder endpoint"""
    return {
        "tickets": [],
        "total": 0,
        "message": "Ticket management system coming soon!"
    }

@app.post("/api/v1/tickets")
async def create_ticket():
    """Create ticket - placeholder endpoint"""
    return {
        "id": "temp_001",
        "status": "created",
        "message": "Ticket creation endpoint coming soon!"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)