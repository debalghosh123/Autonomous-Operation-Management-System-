"""
Career Lab Consulting - Email Service
Send exam results and notifications via Resend API
"""
import httpx
from app.config import settings

RESEND_API_URL = "https://api.resend.com/emails"


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


def _build_followup_email(candidate_name: str) -> str:
    """Build an encouraging 7-day follow-up email reminding candidates they can retake the exam."""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #1a1a2e; color: #eaeaea; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #16213e 0%, #1a1a3e 100%); border-radius: 12px; padding: 35px; border: 1px solid #00d4ff;">
            <h1 style="color: #00d4ff; text-align: center; font-size: 24px;">Career Lab Consulting</h1>
            <h2 style="color: #ffffff; text-align: center; font-size: 20px;">We Believe In You!</h2>
            <hr style="border-color: #00d4ff; margin: 25px 0;">
            <p style="font-size: 16px; line-height: 1.8;">Dear <strong>{candidate_name}</strong>,</p>
            <p style="font-size: 16px; line-height: 1.8;">
                It has been a week since your last Python Evaluation attempt, and we wanted to reach out
                and let you know that we are still rooting for you! Growth takes time, and every step
                forward counts.
            </p>
            <p style="font-size: 16px; line-height: 1.8;">
                We encourage you to give the evaluation another try when you feel ready. Here are a few
                tips to help you prepare:
            </p>
            <ul style="font-size: 15px; line-height: 2; color: #cccccc;">
                <li>Review Python fundamentals and OOP concepts</li>
                <li>Practice with real-world coding challenges</li>
                <li>Focus on AI agent development patterns and frameworks</li>
                <li>Revisit topics where you felt less confident</li>
            </ul>
            <div style="background: #0f3460; border-radius: 10px; padding: 20px; margin: 25px 0; text-align: center;">
                <p style="font-size: 17px; color: #00ff88; margin: 0; font-weight: bold;">
                    You are eligible to retake the exam now!
                </p>
                <p style="color: #aaa; margin-top: 10px; font-size: 14px;">
                    Log in to the evaluation system to start your next attempt.
                </p>
            </div>
            <p style="font-size: 16px; line-height: 1.8;">
                Remember, persistence is the key to success. Many of our top candidates
                succeeded on their second or third attempt. Your next try could be the one!
            </p>
            <p style="font-size: 16px; line-height: 1.8;">
                Wishing you the very best,<br>
                <strong style="color: #00d4ff;">The Career Lab Consulting Team</strong>
            </p>
            <p style="color: #888; font-size: 12px; margin-top: 30px; text-align: center;">
                Career Lab Consulting - Empowering Careers, Building Futures
            </p>
        </div>
    </body>
    </html>
    """


async def send_result_email(to_email: str, candidate_name: str, score: int,
                             total_marks: int, percentage: float, passed: bool) -> bool:
    """Send exam result notification via Resend API."""
    if not settings.RESEND_API_KEY:
        status = "QUALIFIED" if passed else "NOT QUALIFIED"
        print(f"[Email] RESEND_API_KEY not configured. Would send to {to_email}: Score {score}/{total_marks} ({percentage:.1f}%) - {status}")
        return False

    if passed:
        subject = "Congratulations! You've Qualified - Career Lab Consulting"
        html_body = _build_qualified_email(candidate_name, score, total_marks, percentage)
    else:
        subject = "Python Evaluation Results - Career Lab Consulting"
        html_body = _build_not_qualified_email(candidate_name, score, total_marks, percentage)

    try:
        print(f"[Email] Sending to {to_email} via Resend API from {settings.FROM_EMAIL}")
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                RESEND_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": settings.FROM_EMAIL,
                    "to": [to_email],
                    "subject": subject,
                    "html": html_body,
                },
            )

        if response.status_code == 200:
            print(f"[Email] Successfully sent to {to_email}")
            return True
        else:
            print(f"[Email] Resend API error ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"[Email] Error sending to {to_email}: {type(e).__name__}: {e}")
        return False


async def send_followup_email(to_email: str, candidate_name: str) -> bool:
    """Send 7-day follow-up email encouraging the candidate to retake the exam via Resend API."""
    if not settings.RESEND_API_KEY:
        print(f"[Email] RESEND_API_KEY not configured. Would send follow-up to {to_email}: Encouraging {candidate_name} to retake exam")
        return False

    subject = "We're Still Rooting For You! - Career Lab Consulting"
    html_body = _build_followup_email(candidate_name)

    try:
        print(f"[Email] Sending follow-up to {to_email} via Resend API from {settings.FROM_EMAIL}")
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                RESEND_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": settings.FROM_EMAIL,
                    "to": [to_email],
                    "subject": subject,
                    "html": html_body,
                },
            )

        if response.status_code == 200:
            print(f"[Email] Follow-up successfully sent to {to_email}")
            return True
        else:
            print(f"[Email] Resend API error ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"[Email] Error sending follow-up to {to_email}: {type(e).__name__}: {e}")
        return False
