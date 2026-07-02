"""
Career Lab Consulting - Service Tests
Tests for AI, email, WhatsApp, and voice services
"""
import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.groq_service import _generate_fallback_feedback
from app.services.voice_service import process_voice_command
from app.utils.helpers import calculate_percentage, is_passed, hash_password, verify_password


def test_calculate_percentage():
    """Test percentage calculation."""
    assert calculate_percentage(90, 100) == 90.0
    assert calculate_percentage(0, 100) == 0.0
    assert calculate_percentage(100, 100) == 100.0
    assert calculate_percentage(0, 0) == 0.0


def test_is_passed():
    """Test pass/fail determination."""
    assert is_passed(90.0) is True
    assert is_passed(91.0) is True
    assert is_passed(89.9) is False
    assert is_passed(100.0) is True


def test_password_hashing():
    """Test password utilities."""
    password = "test123"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True
    assert verify_password("wrong", hashed) is False


def test_fallback_feedback():
    """Test fallback AI feedback generation."""
    topic_perf = {
        "data_types": {"correct": 3, "total": 4, "percentage": 75.0},
        "functions": {"correct": 1, "total": 2, "percentage": 50.0},
    }
    feedback = _generate_fallback_feedback(70, 100, 70.0, topic_perf)
    assert "Career Lab Consulting" in feedback
    assert "70" in feedback


def test_voice_command_next():
    """Test voice command: next."""
    result = asyncio.get_event_loop().run_until_complete(
        process_voice_command("next question")
    )
    assert result["action"] == "next_question"
    assert result["success"] is True


def test_voice_command_select():
    """Test voice command: select answer."""
    result = asyncio.get_event_loop().run_until_complete(
        process_voice_command("select A")
    )
    assert result["action"] == "select_answer"
    assert result["answer"] == "A"


def test_voice_command_submit():
    """Test voice command: submit."""
    result = asyncio.get_event_loop().run_until_complete(
        process_voice_command("submit exam")
    )
    assert result["action"] == "submit_exam"


def test_voice_command_help():
    """Test voice command: help."""
    result = asyncio.get_event_loop().run_until_complete(
        process_voice_command("help")
    )
    assert result["action"] == "help"
    assert "Available commands" in result["message"]


def test_voice_command_time():
    """Test voice command: time."""
    result = asyncio.get_event_loop().run_until_complete(
        process_voice_command("show time")
    )
    assert result["action"] == "show_time"
