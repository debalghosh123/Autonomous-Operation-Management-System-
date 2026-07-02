"""
Career Lab Consulting - Test Suite
Tests for the Python Evaluation System
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    """Test API health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_home_page():
    """Test landing page loads."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Career Lab Consulting" in response.text


def test_register_page():
    """Test registration page loads."""
    response = client.get("/register")
    assert response.status_code == 200
    assert "Registration" in response.text


def test_admin_login_page():
    """Test admin login page loads."""
    response = client.get("/admin/login")
    assert response.status_code == 200
    assert "Admin Login" in response.text


def test_candidate_registration():
    """Test candidate can register."""
    response = client.post(
        "/register",
        data={"name": "Test User", "email": "test@example.com", "phone": "+1234567890"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "/exam/start/" in response.headers["location"]


def test_api_create_candidate():
    """Test API candidate creation."""
    response = client.post(
        "/api/candidates",
        json={"name": "API User", "email": "api@example.com", "phone": "+9876543210"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "API User"
    assert data["email"] == "api@example.com"


def test_api_list_candidates():
    """Test API list candidates."""
    response = client.get("/api/candidates")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_api_statistics():
    """Test API statistics endpoint."""
    response = client.get("/api/statistics")
    assert response.status_code == 200
    data = response.json()
    assert "total_exams" in data
    assert "pass_rate" in data


def test_voice_command():
    """Test voice command endpoint."""
    response = client.post(
        "/api/voice",
        json={"command": "next"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["action"] == "next_question"
    assert data["success"] is True


def test_voice_help_command():
    """Test voice help command."""
    response = client.post(
        "/api/voice",
        json={"command": "help"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["action"] == "help"


def test_admin_login_fail():
    """Test admin login with wrong credentials."""
    response = client.post(
        "/admin/login",
        data={"username": "wrong", "password": "wrong"},
        follow_redirects=False,
    )
    assert response.status_code == 200  # Stays on login page
    assert "Invalid credentials" in response.text


def test_admin_login_success():
    """Test admin login with correct credentials."""
    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/dashboard"


def test_exam_start():
    """Test starting an exam."""
    # First register a candidate
    reg_response = client.post(
        "/register",
        data={"name": "Exam Tester", "email": "examtester@example.com", "phone": ""},
        follow_redirects=False,
    )
    location = reg_response.headers["location"]
    # Follow redirect to exam start
    response = client.get(location)
    assert response.status_code == 200
    assert "Exam Instructions" in response.text


def test_duplicate_email_handling():
    """Test registering with existing email."""
    response = client.post(
        "/register",
        data={"name": "Duplicate", "email": "test@example.com", "phone": ""},
        follow_redirects=False,
    )
    # Should redirect to existing candidate's exam
    assert response.status_code == 303
