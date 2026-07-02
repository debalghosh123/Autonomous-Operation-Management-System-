"""
Career Lab Consulting - Email Service
Send exam results and notifications via email
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings


async def send_result_email(to_email: str, candidate_name: str, score: int,
                             total_marks: int, percentage: float, passed: bool) -> bool:
    """Send exam result notification via email."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print(f"[Email] Would send to {to_email}: Score {score}/{total_marks} ({percentage:.1f}%)")
        return False

    subject = f"Python Evaluation Results - Career Lab Consulting"
    status = "QUALIFIED" if passed else "NOT QUALIFIED"

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #1a1a2e; color: #eaeaea; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: #16213e; border-radius: 10px; padding: 30px;">
            <h1 style="color: #00d4ff; text-align: center;">Career Lab Consulting</h1>
            <h2 style="color: #ffffff; text-align: center;">Python Evaluation Results</h2>
            <hr style="border-color: #00d4ff;">
            <p>Dear <strong>{candidate_name}</strong>,</p>
            <p>Thank you for completing the Python Evaluation. Here are your results:</p>
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr style="background: #0f3460;">
                    <td style="padding: 10px; border: 1px solid #333;">Score</td>
                    <td style="padding: 10px; border: 1px solid #333;"><strong>{score}/{total_marks}</strong></td>
                </tr>
                <tr style="background: #1a1a2e;">
                    <td style="padding: 10px; border: 1px solid #333;">Percentage</td>
                    <td style="padding: 10px; border: 1px solid #333;"><strong>{percentage:.1f}%</strong></td>
                </tr>
                <tr style="background: #0f3460;">
                    <td style="padding: 10px; border: 1px solid #333;">Status</td>
                    <td style="padding: 10px; border: 1px solid #333;">
                        <strong style="color: {'#00ff88' if passed else '#ff4444'};">{status}</strong>
                    </td>
                </tr>
            </table>
            <p>{'Congratulations! You have qualified for the next round.' if passed else 'We encourage you to review the topics and try again.'}</p>
            <p style="color: #888; font-size: 12px; margin-top: 30px;">
                This is an automated message from Career Lab Consulting Evaluation System.
            </p>
        </div>
    </body>
    </html>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.FROM_EMAIL
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        return True
    except Exception as e:
        print(f"[Email] Error sending to {to_email}: {e}")
        return False
