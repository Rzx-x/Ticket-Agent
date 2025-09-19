# OmniDesk AI Backend – Architecture & Developer Guide

## Overview
OmniDesk AI is a smart IT ticket management backend that consolidates tickets from multiple sources (GLPI, Solman, Email, SMS) into a unified system. It uses AI (Claude + custom models) for classification, urgency detection, and auto-response, and provides real-time analytics for IT staff.

---

## Project Structure
```
omni_desk_backend/
  app/
    api/              # FastAPI routers (endpoints)
    core/             # Config, DB, logging
    integrations/     # Email, SMS, GLPI, Solman
    models/           # SQLAlchemy ORM models
    schemas/          # Pydantic schemas
    services/         # AI, vector search, etc.
    main.py           # FastAPI app entry point
  tests/              # Integration tests
  requirements.txt    # Python dependencies
```

---

## Key Components & How They Link

### 1. `main.py`
- **Entry point** for FastAPI backend.
- Sets up app, CORS, logging, routers, health checks, startup/shutdown events.
- **Links to:** `core/config.py`, `core/database.py`, `core/logging.py`, `api/tickets.py`, `services/ai_service.py`, `services/vector_service.py`, `integrations/email_service.py`, `integrations/sms_service.py`.

### 2. `core/config.py`
- Loads environment variables and settings (DB URLs, API keys, debug flags).
- **Used by:** All modules for configuration.

### 3. `core/database.py`
- Sets up SQLAlchemy engine and `Base` for ORM models.
- Handles DB connection and health checks.
- **Links to:** `models/` (ORM), `main.py` (table creation), Neon (Postgres).

### 4. `core/logging.py`
- Configures logging for the backend.
- **Used by:** `main.py` and other modules.

### 5. `api/tickets.py`
- FastAPI routers for ticket endpoints (CRUD, search, analytics).
- **Links to:** `models/ticket.py`, `schemas/ticket.py`, `core/database.py`, `services/ai_service.py`, `services/vector_service.py`, `integrations/email_service.py`, `integrations/sms_service.py`.

### 6. `models/`
- SQLAlchemy ORM models (e.g., Ticket, TicketInteraction).
- **Links to:** `core/database.py`, `api/tickets.py`, Neon (Postgres).

### 7. `schemas/`
- Pydantic models for request/response validation.
- **Links to:** `api/tickets.py`, `models/`.

### 8. `services/ai_service.py`
- Handles AI classification, urgency detection, auto-response (Claude API, custom models).
- **Links to:** `api/tickets.py`, `core/config.py`.

### 9. `services/vector_service.py`
- Handles semantic search using Qdrant.
- **Links to:** `api/tickets.py`, Qdrant DB.

### 10. `integrations/email_service.py`, `sms_service.py`
- Handle sending/receiving emails and SMS.
- **Links to:** `api/tickets.py`, `core/config.py`.

---

## Database & Vector DB
- **Neon (Postgres):** Stores all ticket data, user info, interactions, etc. Accessed via SQLAlchemy ORM.
- **Qdrant (Vector DB):** Stores vector embeddings for tickets for semantic search. Accessed via Qdrant client in `services/vector_service.py`.

---

## Typical Ticket Flow
1. User submits a ticket (web, email, SMS, etc.).
2. API endpoint in `api/tickets.py` receives the request.
3. Schema validation via Pydantic (`schemas/ticket.py`).
4. AI service classifies ticket, detects urgency/language (`services/ai_service.py`).
5. Ticket is saved to Neon (Postgres) via SQLAlchemy (`models/ticket.py`).
6. Vector embedding is generated and stored in Qdrant (`services/vector_service.py`).
7. Auto-response is sent via email/SMS if needed (`integrations/`).
8. IT staff can view/manage tickets via dashboard endpoints.
9. Analytics/search endpoints use both Neon and Qdrant.

---

## How to Run the Backend
1. **Install dependencies:**
   ```sh
   cd omni_desk_backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r ../requirements.txt
   ```
2. **Set up environment variables:**
   - Create a `.env` file in `app/core/` or project root with DB URLs, API keys, etc.
3. **Start the server:**
   ```sh
   uvicorn app.main:app --reload
   ```
   - Or, for direct script run: `python app/main.py`
4. **API docs:**
   - Visit [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Testing
- Run integration tests after starting the server:
  ```sh
  cd omni-desk-backend/tests
  python test_api.py
  ```

---

## Troubleshooting
- **ModuleNotFoundError: No module named 'app'**
  - Make sure you run uvicorn from the `omni_desk_backend` directory.
  - Use `PYTHONPATH=. uvicorn app.main:app --reload` if needed.
- **Permission denied**
  - Fix with `chmod -R u+rwx omni-desk-backend/`
- **Address already in use**
  - Kill the process on port 8000: `lsof -i :8000` then `kill -9 <PID>`
- **Database connection errors**
  - Check your Neon (Postgres) URL and credentials in `.env`.
- **Qdrant errors**
  - Ensure Qdrant is running and accessible; check its URL in `.env`.

---

## Useful Tips
- Always activate your virtual environment before running the backend.
- Keep your `.env` file secure and never commit secrets to git.
- Use the `/health` and `/api/v1/system/info` endpoints to check backend status.
- For new features, add Pydantic schemas, update routers, and link to models/services as needed.
- Use logging for debugging and monitoring.

---

## Further Reading
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Qdrant Docs](https://qdrant.tech/documentation/)
- [Neon Postgres](https://neon.tech/docs/introduction/)

---

## Contact
For questions or contributions, open an issue or PR on the project repo.
