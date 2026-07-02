"""
Career Lab Consulting - Helper Utilities
"""
import hashlib
import secrets
from datetime import datetime, timedelta


def hash_password(password: str) -> str:
    """Simple password hashing."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(password) == hashed


def generate_token() -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(32)


def format_duration(start: datetime, end: datetime) -> str:
    """Format time duration in human-readable format."""
    delta = end - start
    minutes = int(delta.total_seconds() / 60)
    seconds = int(delta.total_seconds() % 60)
    return f"{minutes}m {seconds}s"


def calculate_percentage(score: int, total: int) -> float:
    """Calculate percentage."""
    if total == 0:
        return 0.0
    return round((score / total) * 100, 2)


def is_passed(percentage: float, passing_percentage: float = 90.0) -> bool:
    """Check if candidate has passed based on passing percentage."""
    return percentage >= passing_percentage
