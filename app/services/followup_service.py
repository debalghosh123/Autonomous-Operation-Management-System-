"""
Career Lab Consulting - Follow-up Service
Automatically checks for due follow-up notifications and sends emails.
No external cron or scheduler needed - checks are triggered on home page visits.
"""
import time
from datetime import datetime
from app.database import get_db
from app.services.email_service import send_followup_email

# Module-level timestamp to throttle checks to once per hour
_last_check_time: float = 0.0
_CHECK_INTERVAL_SECONDS = 3600  # 1 hour


async def check_and_send_followups() -> None:
    """
    Check for due follow-up notifications and send emails.
    Only performs the check once per hour to avoid excessive DB queries.
    """
    global _last_check_time

    now = time.time()
    if now - _last_check_time < _CHECK_INTERVAL_SECONDS:
        return

    _last_check_time = now

    try:
        with get_db() as db:
            # Find all follow-up notifications that are due
            due_notifications = db.execute("""
                SELECT n.id, n.candidate_id, c.email, c.name
                FROM notifications n
                JOIN candidates c ON c.id = n.candidate_id
                WHERE n.type = 'follow_up_7day'
                  AND n.status = 'scheduled'
                  AND n.scheduled_at <= ?
            """, (datetime.utcnow().isoformat(),)).fetchall()

            for notification in due_notifications:
                try:
                    await send_followup_email(notification["email"], notification["name"])
                    db.execute(
                        "UPDATE notifications SET status = 'sent', sent_at = ? WHERE id = ?",
                        (datetime.utcnow().isoformat(), notification["id"])
                    )
                except Exception as e:
                    print(f"[FollowUp] Error sending follow-up to {notification['email']}: {type(e).__name__}: {e}")

    except Exception as e:
        print(f"[FollowUp] Error checking follow-ups: {type(e).__name__}: {e}")
