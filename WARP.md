# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

OmniDesk AI is a smart IT ticket management system that consolidates tickets from multiple sources (GLPI, Solman, Email, SMS) into a unified web application. The system uses AI (Claude + custom models) to classify, prioritize, and auto-respond to employee issues with multi-language support (English/Hindi mix).

## Architecture

**Backend (FastAPI)**: Python-based API server in `backend/` directory
- Modular architecture with separate layers: API routes, services, models, and integrations
- Core services: AI classification, vector search, language detection, ticket management
- External integrations: Claude API, GLPI, Solman, Email (SMTP), SMS (Twilio)
- Database: PostgreSQL (Neon) with Alembic migrations
- Vector search: Qdrant for semantic ticket similarity

**Frontend (React)**: Vite + React + TypeScript application in `frontend/ai-desk-central-main/`
- Modern UI with shadcn/ui components and Tailwind CSS
- Features: Real-time dashboard, ticket submission interface, analytics

**Database Schema**: Comprehensive ticket management with AI analytics
- Main entities: Tickets, TicketResponses, TicketAnalytics, KnowledgeBase
- Supports multi-source ticket ingestion and AI-powered classification

## Development Commands

### Backend Development
```powershell
# Install dependencies
pip install -r backend/requirements.txt

# Setup environment (creates tables, tests connections)
python scripts/setup_env.py

# Run database migrations
alembic upgrade head

# Start development server
uvicorn backend.app.main:app --reload

# Run tests
pytest backend/tests/ -v

# Test individual components
python scripts/smoke_db_test.py
python scripts/test_config.py

# Health check
curl http://localhost:8000/health
```

### Frontend Development
```powershell
# Navigate to frontend directory
cd frontend/ai-desk-central-main

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Lint code
npm run lint

# Preview production build
npm run preview
```

### Docker Development
```powershell
# Run full stack with local databases
docker-compose up

# Run backend only
docker-compose up backend

# Run with specific services
docker-compose up backend db qdrant
```

### Database Operations
```powershell
# Create new migration
alembic revision --autogenerate -m "description"

# Upgrade to latest
alembic upgrade head

# Downgrade one revision
alembic downgrade -1

# View current revision
alembic current

# View migration history
alembic history
```

## Environment Configuration

Copy `backend/.env.example` to `.env` and configure:

**Required for development:**
- `DATABASE_URL`: PostgreSQL connection string
- `ANTHROPIC_API_KEY`: Claude API key for AI services
- `QDRANT_URL` and `QDRANT_API_KEY`: Vector database connection

**Optional integrations:**
- SMTP settings for email integration
- Twilio credentials for SMS support
- GLPI/Solman API credentials for external ticket systems

## Key Services Architecture

**AI Pipeline Flow:**
1. Language detection → Category classification → Urgency assessment → Solution generation
2. Vector similarity search for related tickets and knowledge base articles
3. Multi-language response generation (English/Hindi mix support)

**Ticket Processing:**
1. Ingestion from multiple sources (web, email, SMS, GLPI, Solman)
2. AI classification and auto-response generation
3. Vector embedding storage for similarity matching
4. Analytics tracking and dashboard updates

**Service Dependencies:**
- `ai_service.py`: Claude API integration for classification and responses
- `vector_service.py`: Qdrant client for semantic search
- `language_detector.py`: Multi-language text analysis
- `ticket_services.py`: Core business logic for ticket management

## Testing Strategy

**Backend Tests:**
- `test_api.py`: API endpoint testing
- `test_database.py`: Database operations and models
- `test_health.py`: Health check functionality

**Development Testing:**
- Use `scripts/setup_env.py` for comprehensive environment validation
- Health endpoints available at `/health` and `/api/v1/system/info`
- All services include availability checks for graceful degradation

## Common Development Tasks

**Adding New Ticket Sources:**
1. Create integration service in `backend/app/integrations/`
2. Add source enum to `TicketSource` in `db/models.py`
3. Update ticket ingestion logic in `ticket_services.py`
4. Add configuration variables to `.env.example`

**Modifying AI Classification:**
1. Update prompts and logic in `ai_service.py`
2. Adjust category/urgency enums in models if needed
3. Test classification accuracy with sample data
4. Update vector embeddings for improved similarity matching

**Frontend Component Development:**
- Components use shadcn/ui with Radix primitives
- State management with React Query (@tanstack/react-query)
- Routing with React Router DOM
- Styling with Tailwind CSS and class-variance-authority

## Deployment Configuration

**Backend**: Configured for Railway deployment
- `Procfile`: Defines start command for production
- `railway.json`: Railway-specific configuration
- Environment variables configured in Railway dashboard

**Frontend**: Configured for Vercel deployment
- Vite build system optimized for production
- Environment variables for API endpoints

**Database**: Neon PostgreSQL with connection pooling
**Vector Search**: Qdrant Cloud integration