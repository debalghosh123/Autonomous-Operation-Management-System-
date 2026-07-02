"""
Career Lab Consulting - Database Tests
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db, get_db


def test_database_init():
    """Test database initialization creates tables."""
    init_db()
    with get_db() as db:
        # Check tables exist
        tables = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t["name"] for t in tables]
        assert "candidates" in table_names
        assert "exams" in table_names
        assert "questions" in table_names
        assert "answers" in table_names
        assert "admin_logs" in table_names
        assert "notifications" in table_names


def test_questions_seeded():
    """Test 25 questions are seeded."""
    init_db()
    with get_db() as db:
        count = db.execute("SELECT COUNT(*) as c FROM questions").fetchone()["c"]
        assert count == 25


def test_questions_have_4_marks():
    """Test all questions have 4 marks."""
    with get_db() as db:
        questions = db.execute("SELECT marks FROM questions").fetchall()
        for q in questions:
            assert q["marks"] == 4


def test_total_marks_is_100():
    """Test total marks across all questions is 100."""
    with get_db() as db:
        total = db.execute("SELECT SUM(marks) as total FROM questions").fetchone()["total"]
        assert total == 100
