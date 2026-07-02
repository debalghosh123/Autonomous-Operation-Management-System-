"""
Career Lab Consulting - WhatsApp Service
Send exam notifications via WhatsApp using Twilio
"""
import httpx
from app.config import settings


async def send_whatsapp_notification(to_phone: str, candidate_name: str,
                                      score: int, total_marks: int,
                                      percentage: float, passed: bool) -> bool:
    """Send exam result notification via WhatsApp."""
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        print(f"[WhatsApp] Would send to {to_phone}: Score {score}/{total_marks} ({percentage:.1f}%)")
        return False

    status = "QUALIFIED" if passed else "NOT QUALIFIED"
    message = (
        f"*Career Lab Consulting - Python Evaluation*\n\n"
        f"Dear {candidate_name},\n\n"
        f"Your evaluation results:\n"
        f"- Score: {score}/{total_marks}\n"
        f"- Percentage: {percentage:.1f}%\n"
        f"- Status: {status}\n\n"
        f"{'Congratulations! You have qualified.' if passed else 'Keep practicing and try again!'}\n\n"
        f"- Career Lab Consulting Team"
    )

    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
                data={
                    "From": f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
                    "To": f"whatsapp:{to_phone}",
                    "Body": message,
                },
            )
            return response.status_code == 201
    except Exception as e:
        print(f"[WhatsApp] Error sending to {to_phone}: {e}")
        return False
