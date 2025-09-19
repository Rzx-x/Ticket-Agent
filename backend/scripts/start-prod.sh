#!/bin/bash
set -e

echo "🚀 Starting OmniDesk AI Backend in Production Mode"

# Wait for database to be ready
echo "⏳ Waiting for database connection..."
python -c "
import time
import sys
from app.core.database import test_db_connection

max_tries = 30
for i in range(max_tries):
    try:
        if test_db_connection():
            print('✅ Database connection successful')
            break
    except Exception as e:
        print(f'❌ Database connection failed (attempt {i+1}/{max_tries}): {e}')
        if i == max_tries - 1:
            print('💥 Failed to connect to database after 30 attempts')
            sys.exit(1)
        time.sleep(2)
"

# Run database migrations
echo "🔄 Running database migrations..."
python -c "
from app.core.database import engine, Base
try:
    Base.metadata.create_all(bind=engine)
    print('✅ Database migrations completed')
except Exception as e:
    print(f'❌ Migration failed: {e}')
    exit(1)
"

# Initialize vector database
echo "🧠 Initializing vector database..."
python -c "
from app.services.vector_service import vector_service
try:
    if vector_service.is_available():
        print('✅ Vector database initialized')
    else:
        print('⚠️ Vector database not available')
except Exception as e:
    print(f'⚠️ Vector database initialization warning: {e}')
"

# Start the application with gunicorn for production
echo "🎉 Starting application server..."
exec gunicorn app.main:app \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 30 \
    --keep-alive 2 \
    --access-logfile /app/logs/access.log \
    --error-logfile /app/logs/error.log \
    --log-level info \
    --preload