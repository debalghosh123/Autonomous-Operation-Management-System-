"""
Career Lab Consulting - Test Suite
Tests for the Python Evaluation System
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app
from datetime import datetime, timedelta
from app.database import get_db

client = TestClient(app)


def _admin_login(test_client):
    """Helper to login as admin and return the client with session cookie."""
    test_client.post(
        "/admin/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=False,
    )
    return test_client


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
    test_client = TestClient(app)
    response = test_client.post(
        "/admin/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/dashboard"
    # Verify session allows access to dashboard
    dashboard_response = test_client.get("/admin/dashboard", follow_redirects=False)
    assert dashboard_response.status_code == 200


def test_admin_dashboard_requires_auth():
    """Test that admin dashboard redirects to login when not authenticated."""
    test_client = TestClient(app)
    response = test_client.get("/admin/dashboard", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"


def test_admin_candidates_requires_auth():
    """Test that admin candidates page redirects to login when not authenticated."""
    test_client = TestClient(app)
    response = test_client.get("/admin/candidates", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"


def test_admin_questions_requires_auth():
    """Test that admin questions page redirects to login when not authenticated."""
    test_client = TestClient(app)
    response = test_client.get("/admin/questions", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"


def test_admin_dashboard_accessible_after_login():
    """Test that admin dashboard is accessible after login."""
    test_client = TestClient(app)
    _admin_login(test_client)
    response = test_client.get("/admin/dashboard", follow_redirects=False)
    assert response.status_code == 200


def test_admin_candidates_accessible_after_login():
    """Test that admin candidates page is accessible after login."""
    test_client = TestClient(app)
    _admin_login(test_client)
    response = test_client.get("/admin/candidates", follow_redirects=False)
    assert response.status_code == 200


def test_admin_questions_accessible_after_login():
    """Test that admin questions page is accessible after login."""
    test_client = TestClient(app)
    _admin_login(test_client)
    response = test_client.get("/admin/questions", follow_redirects=False)
    assert response.status_code == 200


def test_admin_logout():
    """Test admin logout clears session."""
    test_client = TestClient(app)
    _admin_login(test_client)
    # Verify logged in
    response = test_client.get("/admin/dashboard", follow_redirects=False)
    assert response.status_code == 200
    # Logout
    response = test_client.get("/admin/logout", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"
    # Verify no longer authenticated
    response = test_client.get("/admin/dashboard", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"


def test_exam_cooldown():
    """Test 14-day cooldown prevents starting a new exam."""
    # Register a new candidate for this test
    test_client = TestClient(app)
    reg_response = test_client.post(
        "/register",
        data={"name": "Cooldown Tester", "email": "cooldown@example.com", "phone": "+1111111111"},
        follow_redirects=False,
    )
    location = reg_response.headers["location"]
    candidate_id = int(location.split("/")[-1])

    # Manually insert a completed exam with recent completed_at
    with get_db() as db:
        recent_time = datetime.now().isoformat()
        db.execute(
            "INSERT INTO exams (candidate_id, total_marks, completed_at, score, percentage, passed) VALUES (?, ?, ?, ?, ?, ?)",
            (candidate_id, 100, recent_time, 50, 50.0, 0),
        )

    # Try to start a new exam - should show cooldown message
    response = test_client.get(f"/exam/start/{candidate_id}")
    assert response.status_code == 200
    assert "cooldown" in response.text.lower() or "retake" in response.text.lower() or "after" in response.text.lower()


def test_exam_start():
    """Test starting an exam."""
    # First register a candidate
    reg_response = client.post(
        "/register",
        data={"name": "Exam Tester", "email": "examtester@example.com", "phone": "+2222222222"},
        follow_redirects=False,
    )
    location = reg_response.headers["location"]
    # Follow redirect to exam start
    response = client.get(location)
    assert response.status_code == 200


def test_admin_exam_detail_requires_auth():
    """Test that admin exam detail page redirects to login when not authenticated."""
    test_client = TestClient(app)
    response = test_client.get("/admin/exam/1", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"


def test_follow_up_notification_created_on_failure():
    """Test that a follow_up_7day notification is created when a candidate fails."""
    test_client = TestClient(app)

    # Register a candidate
    reg_response = test_client.post(
        "/register",
        data={"name": "Notification Tester", "email": "notify_test@example.com", "phone": "+3333333333"},
        follow_redirects=False,
    )
    location = reg_response.headers["location"]
    candidate_id = int(location.split("/")[-1])

    # Start an exam
    start_response = test_client.get(f"/exam/start/{candidate_id}")
    assert start_response.status_code == 200

    # Submit the exam using the new serverless-safe endpoint with hidden fields
    # Submit with wrong answers to guarantee failure
    submit_response = test_client.post(
        "/exam/submit",
        data={
            "total_questions": "1",
            "candidate_name": "Notification Tester",
            "candidate_email": "notify_test@example.com",
            "candidate_phone": "+3333333333",
            "correct_1": "A",
            "topic_1": "python",
            "marks_1": "4",
            "question_1": "B",  # Wrong answer (correct is A)
        },
        follow_redirects=False,
    )
    assert submit_response.status_code == 200  # Direct render (no redirect)
    assert "NOT QUALIFIED" in submit_response.text or "Improvement Needed" in submit_response.text

    # Verify a follow_up_7day notification was created
    with get_db() as db:
        notification = db.execute(
            "SELECT * FROM notifications WHERE candidate_id = ? AND type = 'follow_up_7day'",
            (candidate_id,)
        ).fetchone()
        assert notification is not None
        assert notification["status"] == "scheduled"
        assert "follow-up" in notification["message"].lower() or "Follow-up" in notification["message"]


def test_duplicate_email_handling():
    """Test registering with existing email."""
    response = client.post(
        "/register",
        data={"name": "Duplicate", "email": "test@example.com", "phone": "+4444444444"},
        follow_redirects=False,
    )
    # Should redirect to existing candidate's exam
    assert response.status_code == 303
