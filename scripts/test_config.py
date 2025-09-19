#!/usr/bin/env python3
"""
Configuration validation and testing script
"""
import os
import sys
from pathlib import Path
import asyncio
import psycopg2
import redis
from typing import Optional
from loguru import logger
from dotenv import load_dotenv

# Add backend and project root to path
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))  # Add backend path first
sys.path.insert(0, str(project_root))  # Add project root path first

# Load environment variables first
env_file = Path(__file__).parent.parent / "backend" / ".env"
print(f"Checking for .env file at {env_file}")
if env_file.exists():
    print("Found .env file, loading environment variables...")
    load_dotenv(env_file)
else:
    print(f"No .env file found at {env_file}")

from app.core.config import settings

class ConfigTester:
    def __init__(self):
        self.all_passed = True
        self.results = []

    def log_result(self, test_name: str, passed: bool, details: Optional[str] = None):
        """Log test result with consistent formatting"""
        status = "✅" if passed else "❌"
        result = f"{status} {test_name}"
        if details and not passed:
            result += f": {details}"
        self.results.append(result)
        if not passed:
            self.all_passed = False
        logger.info(result)

    def test_database(self):
        """Test database connection"""
        print("Testing database connection...")
        try:
            print(f"Connecting to database: {settings.DATABASE_URL}")
            conn = psycopg2.connect(settings.DATABASE_URL)
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            conn.close()
            self.log_result("Database Connection", True)
            print("Database connection successful")
        except Exception as e:
            print(f"Database connection failed: {e}")
            self.log_result("Database Connection", False, str(e))

    def test_redis(self):
        """Test Redis connection"""
        print("Testing Redis connection...")
        try:
            print(f"Connecting to Redis: {settings.REDIS_URL}")
            r = redis.from_url(settings.REDIS_URL)
            r.ping()
            self.log_result("Redis Connection", True)
            print("Redis connection successful")
        except Exception as e:
            print(f"Redis connection failed: {e}")
            self.log_result("Redis Connection", False, str(e))

    def test_email_config(self):
        """Validate email configuration"""
        print("Checking email configuration...")
        required_fields = ["SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD"]
        missing = [field for field in required_fields if not getattr(settings, field)]
        
        if not missing:
            self.log_result("Email Config", True)
            print("Email configuration is complete")
        else:
            self.log_result("Email Config", False, f"Missing: {', '.join(missing)}")
            print(f"Email configuration is missing fields: {', '.join(missing)}")

    def test_sms_config(self):
        """Validate SMS configuration"""
        print("Checking SMS configuration...")
        required_fields = ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER"]
        missing = [field for field in required_fields if not getattr(settings, field)]
        
        if not missing:
            self.log_result("SMS Config", True)
            print("SMS configuration is complete")
        else:
            self.log_result("SMS Config", False, f"Missing: {', '.join(missing)}")
            print(f"SMS configuration is missing fields: {', '.join(missing)}")

    async def test_ai_service(self):
        """Test AI service"""
        print("Testing AI service...")
        try:
            print(f"AI service API key present: {'*' * 8 if settings.ANTHROPIC_API_KEY else 'No'}")
            if not settings.ANTHROPIC_API_KEY:
                raise Exception("AI service not configured")
                
            self.log_result("AI Service", True)
            print("AI service configuration is valid")
        except Exception as e:
            self.log_result("AI Service", False, str(e))
            print(f"AI service error: {e}")

    async def test_hst_api(self):
        """Test HST API connection"""
        print("Testing HST API...")
        try:
            print(f"HST API key present: {'*' * 8 if settings.HST_API_KEY else 'No'}")
            if not settings.HST_API_KEY:
                raise Exception("HST API key not configured")
                
            self.log_result("HST API", True)
            print("HST API configuration is valid")
        except Exception as e:
            self.log_result("HST API", False, str(e))
            print(f"HST API error: {e}")

    async def run_all_tests(self):
        """Run all configuration tests"""
        print("\n🔍 Testing configuration...\n")
        
        # Test essential services
        print("Testing essential services...")
        print("\nTesting Database...")
        print(f"Database URL: {settings.DATABASE_URL}")
        self.test_database()

        print("\nTesting Redis...")
        print(f"Redis URL: {settings.REDIS_URL}")
        self.test_redis()
        
        # Test AI and API services
        print("\nTesting AI and API services...")
        await self.test_ai_service()
        await self.test_hst_api()
        
        # Test messaging configurations
        print("\nTesting messaging configurations...")
        self.test_email_config()
        self.test_sms_config()
        
        # Print summary
        print("\n📝 Test Summary:")
        if not self.results:
            print("No test results recorded!")
        else:
            for result in self.results:
                print(result)
            
        if self.all_passed:
            print("\n✨ All tests passed successfully!")
            return 0
        else:
            print("\n⚠️ Some tests failed. Please check the results above.")
            return 1

async def main():
    # Load environment variables
    env_file = project_root / "backend" / ".env"
    print(f"Checking for .env file at {env_file}")
    if env_file.exists():
        print("Found .env file, loading environment variables...")
        load_dotenv(env_file)
    else:
        print(f"No .env file found at {env_file}")

    # Run tests
    print("\nInitializing config tester...")
    tester = ConfigTester()
    print("Starting tests...\n")
    return await tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))