import pytest
from backend.app.core.database import test_db_connection

def test_database_connection():
    assert test_db_connection() is True
