"""
Career Lab Consulting - Test Configuration
Shared fixtures for testing
"""
import sys
import os
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app
from app.database import init_db

# Ensure database is initialized for tests (in production this happens via startup event)
init_db()


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def sample_candidate():
    """Sample candidate data for testing."""
    return {
        "name": "Test Candidate",
        "email": "fixture@example.com",
        "phone": "+1234567890",
    }
