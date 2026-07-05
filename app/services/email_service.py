"""
Career Lab Consulting - Email Service
Send exam results and notifications via email
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings


def _build_qualified_email(candidate_name: str, score: int, total_marks: int, percentage: float) -> str:
    """Build a warm, celebratory welcome email for qualified candidates."""
    return f"""
    <html>
    <body style="font-family: 'Georgia', serif; background-color: #0d1b2a; color: #eaeaea; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #1b3a4b 0%, #065a60 100%); border-radius: 15px; padding: 40px; border: 2px solid #00d4ff;">
            <h1 style="color: #ffd700; text-align: center; font-size: 28px;">Congratulations, {candidate_name}!</h1>
            <div style="text-align: center; font-size: 48px; margin: 20px 0;">&#127881; &#127775; &#127881;</div>
            <h2 style="color: #00ff88; text-align: center;">You Have Been Qualified!</h2>
            <hr style="border-color: #ffd700; margin: 25px 0;">
            <p style="font-size: 16px; line-height: 1.8;">Dear <strong>{candidate_name}</strong>,</p>
            <p style="font-size: 16px; line-height: 1.8;">
                We are absolutely thrilled to share this wonderful news with you! You have successfully
                cleared the Python Evaluation with flying colors, scoring an impressive
                <strong style="color: #00ff88;">{score}/{total_marks} ({percentage:.1f}%)</strong>.
            </p>
            <p style="font-size: 16px; line-height: 1.8;">
                Your dedication, hard work, and brilliant problem-solving skills have truly shone through.
                Welcome aboard to the next exciting chapter of your journey with
                <strong style="color: #ffd700;">Career Lab Consulting</strong>!
            </p>
            <p style="font-size: 16px; line-height: 1.8;">
                We are delighted to welcome you to the next stage of our selection process.
                Our team will be reaching out to you shortly with further details about what
                comes next. Get ready for an amazing experience ahead!
            </p>
            <div style="background: #0f3460; border-radius: 10px; padding: 20px; margin: 25px 0; text-align: center;">
                <p style="font-size: 18px; color: #ffd700; margin: 0;">
                    "The future belongs to those who believe in the beauty of their dreams."
                </p>
                <p style="color: #aaa; margin-top: 10px;">Welcome to the Career Lab family!</p>
            </div>
            <p style="font-size: 16px; line-height: 1.8;">
                With warm regards and heartfelt congratulations,<br>
                <strong style="color: #00d4ff;">The Career Lab Consulting Team</strong>
            </p>
            <p style="color: #888; font-size: 12px; margin-top: 30px; text-align: center;">
                Career Lab Consulting - Empowering Careers, Building Futures
            </p>
        </div>
    </body>
    </html>
    """


def _build_not_qualified_email(candidate_name: str, score: int, total_marks: int, percentage: float) -> str:
    """Build a professional, encouraging email for not-qualified candidates with 7-day follow-up mention."""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #1a1a2e; color: #eaeaea; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: #16213e; border-radius: 10px; padding: 30px;">
            <h1 style="color: #00d4ff; text-align: center;">Career Lab Consulting</h1>
            <h2 style="color: #ffffff; text-align: center;">Python Evaluation Results</h2>
            <hr style="border-color: #00d4ff;">
            <p style="font-size: 16px; line-height: 1.8;">Dear <strong>{candidate_name}</strong>,</p>
            <p style="font-size: 16px; line-height: 1.8;">
                Thank you for taking the time to complete the Python Evaluation at Career Lab Consulting.
                We truly appreciate the effort and commitment you demonstrated throughout the assessment.
            </p>
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
                        <strong style="color: #ff9944;">Not Qualified (This Attempt)</strong>
                    </td>
                </tr>
            </table>
            <p style="font-size: 16px; line-height: 1.8;">
                While you did not meet the qualifying threshold this time, please do not be discouraged.
                Every great developer has faced setbacks on their journey. What matters is the persistence
                and willingness to keep improving.
            </p>
            <p style="font-size: 16px; line-height: 1.8;">
                We encourage you to review the key topics, practice consistently, and come back stronger.
                You are welcome to reattempt the evaluation after the cooldown period.
            </p>
            <div style="background: #0f3460; border-radius: 10px; padding: 20px; margin: 25px 0;">
                <p style="font-size: 16px; color: #00d4ff; margin: 0;">
                    <strong>What happens next?</strong>
                </p>
                <p style="font-size: 15px; margin-top: 10px;">
                    Our team will follow up with you after <strong>7 days</strong> regarding
                    the next interview opportunity and to discuss how we can support your preparation
                    for future assessments.
                </p>
            </div>
            <p style="font-size: 16px; line-height: 1.8;">
                Keep learning, keep growing. We believe in your potential!
            </p>
            <p style="font-size: 16px; line-height: 1.8;">
                Best regards,<br>
                <strong style="color: #00d4ff;">The Career Lab Consulting Team</strong>
            </p>
            <p style="color: #888; font-size: 12px; margin-top: 30px; text-align: center;">
                This is an automated message from Career Lab Consulting Evaluation System.
            </p>
        </div>
    </body>
    </html>
    """


async def send_result_email(to_email: str, candidate_name: str, score: int,
                             total_marks: int, percentage: float, passed: bool) -> bool:
    """Send exam result notification via email."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        status = "QUALIFIED" if passed else "NOT QUALIFIED"
        print(f"[Email] Would send to {to_email}: Score {score}/{total_marks} ({percentage:.1f}%) - {status}")
        return False

    if passed:
        subject = "Congratulations! You've Qualified - Career Lab Consulting"
        html_body = _build_qualified_email(candidate_name, score, total_marks, percentage)
    else:
        subject = "Python Evaluation Results - Career Lab Consulting"
        html_body = _build_not_qualified_email(candidate_name, score, total_marks, percentage)

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
