"""
Career Lab Consulting - Notification Service
Unified notification handling for email and WhatsApp
"""
from app.database import get_db
from app.services.email_service import send_result_email
from app.services.whatsapp_service import send_whatsapp_notification


async def send_all_notifications(candidate_id: int, score: int,
                                   total_marks: int, percentage: float, passed: bool):
    """Send notifications via all configured channels."""
    with get_db() as db:
        candidate = db.execute(
            "SELECT * FROM candidates WHERE id = ?", (candidate_id,)
        ).fetchone()
        if not candidate:
            return {"email": False, "whatsapp": False}

    results = {"email": False, "whatsapp": False}

    # Send email
    try:
        results["email"] = await send_result_email(
            candidate["email"], candidate["name"],
            score, total_marks, percentage, passed
        )
    except Exception:
        results["email"] = False

    # Send WhatsApp if phone is available
    if candidate["phone"]:
        try:
            results["whatsapp"] = await send_whatsapp_notification(
                candidate["phone"], candidate["name"],
                score, total_marks, percentage, passed
            )
        except Exception:
            results["whatsapp"] = False

    # Log notification attempts
    with get_db() as db:
        for channel, success in results.items():
            db.execute(
                "INSERT INTO notifications (candidate_id, type, message, status) VALUES (?, ?, ?, ?)",
                (
                    candidate_id,
                    channel,
                    f"Result notification: {score}/{total_marks} ({percentage:.1f}%)",
                    "sent" if success else "failed",
                ),
            )

    return results
