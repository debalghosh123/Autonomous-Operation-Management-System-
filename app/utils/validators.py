"""
Career Lab Consulting - Input Validators
Validation utilities for forms and API inputs
"""
import re


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """Validate phone number format."""
    if not phone:
        return True  # Phone is optional
    pattern = r'^\+?[\d\s-]{10,15}$'
    return bool(re.match(pattern, phone))


def validate_name(name: str) -> bool:
    """Validate candidate name."""
    if not name or len(name.strip()) < 2:
        return False
    if len(name) > 100:
        return False
    return True


def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS."""
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Escape special characters
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#x27;')
    return text.strip()
