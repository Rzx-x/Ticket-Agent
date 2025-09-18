import os
import asyncio
from sqlalchemy import text
from db.database import engine
from db.models import Base
from ai.vector_store import vector_store
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_environment():
    print("🚀 Setting up OmniDesk AI Environment...")

    # 1. Test database connection
    print("📊 Testing database connection...")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

    # 2. Create tables
    print("📋 Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created")
    except Exception as e:
        print(f"❌ Table creation failed: {e}")
        return False

    # 3. Test Qdrant connection
    print("🔍 Testing Qdrant vector database...")
    try:
        collections = vector_store.client.get_collections()
        print(f"✅ Qdrant connection successful. Collections: {len(collections.collections)}")
    except Exception as e:
        print(f"❌ Qdrant connection failed: {e}")
        return False

    # 4. Test Claude API
    print("🤖 Testing Claude API...")
    try:
        from ai.claude_service import claude_service
        test_response = await claude_service.classify_ticket(
            "Test ticket for API verification",
            {"primary_language": "english", "is_mixed": False, "confidence": 1.0}
        )
        print("✅ Claude API connection successful")
    except Exception as e:
        print(f"❌ Claude API failed: {e}")
        return False

    # 5. Populate sample data
    print("📝 Creating sample data...")
    try:
        await create_sample_data()
        print("✅ Sample data created")
    except Exception as e:
        print(f"❌ Sample data creation failed: {e}")
        return False

    print("🎉 Environment setup completed successfully!")
    return True

async def create_sample_data():
    from db.database import SessionLocal
    from db.models import Ticket, KnowledgeBase, TicketAnalytics
    from datetime import datetime

    db = SessionLocal()
    try:
        ticket = Ticket(
            ticket_number="TKT-20250918-000001",
            title="VPN connection not working",
            description="VPN nahi chal raha hai office se connect karne ke liye.",
            source="email",
            user_email="employee1@powergrid.in",
            user_name="Rajesh Kumar",
            user_department="IT"
        )
        db.add(ticket)
        db.commit()
        db.add(TicketAnalytics(ticket_id=ticket.id))
        db.commit()

        kb = KnowledgeBase(
            title="VPN Troubleshooting",
            content="Steps to check VPN connection",
            solution="Verify network, restart VPN client, check credentials."
        )
        db.add(kb)
        db.commit()
        print("✅ Sample ticket and KB entry created")
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating sample data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(setup_environment())
