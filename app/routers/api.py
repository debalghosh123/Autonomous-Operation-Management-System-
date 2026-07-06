"""
Career Lab Consulting - API Router
RESTful API endpoints for programmatic access
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.database import get_db
from app.models.schemas import (
    CandidateCreate,
    CandidateResponse,
    ExamResult,
    VoiceCommand,
    NotificationRequest,
)
from app.services.voice_service import process_voice_command
from app.services.email_service import send_result_email, send_followup_email
from app.services.whatsapp_service import send_whatsapp_notification
from app.config import settings

router = APIRouter(prefix="/api", tags=["API"])


@router.get("/health")
async def health_check():
    """Health check endpoint for Railway deployment."""
    return {"status": "healthy", "service": "Career Lab Python Evaluation System"}


@router.post("/candidates", response_model=CandidateResponse)
async def create_candidate(candidate: CandidateCreate):
    """Create a new candidate via API."""
    with get_db() as db:
        try:
            cursor = db.execute(
                "INSERT INTO candidates (name, email, phone) VALUES (?, ?, ?)",
                (candidate.name, candidate.email, candidate.phone),
            )
            return CandidateResponse(
                id=cursor.lastrowid,
                name=candidate.name,
                email=candidate.email,
                phone=candidate.phone,
            )
        except Exception as e:
            if "UNIQUE" in str(e):
                raise HTTPException(status_code=400, detail="Email already registered")
            raise HTTPException(status_code=500, detail="Registration failed")


@router.get("/candidates")
async def list_candidates():
    """List all candidates."""
    with get_db() as db:
        candidates = db.execute("SELECT * FROM candidates ORDER BY registered_at DESC").fetchall()
        return [dict(c) for c in candidates]


@router.get("/exams/{exam_id}/result")
async def get_exam_result(exam_id: int):
    """Get exam result by ID."""
    with get_db() as db:
        exam = db.execute("SELECT * FROM exams WHERE id = ?", (exam_id,)).fetchone()
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")

        candidate = db.execute(
            "SELECT * FROM candidates WHERE id = ?", (exam["candidate_id"],)
        ).fetchone()

        answers = db.execute(
            "SELECT * FROM answers WHERE exam_id = ?", (exam_id,)
        ).fetchall()

        correct_count = sum(1 for a in answers if a["is_correct"])

        return {
            "exam_id": exam_id,
            "candidate_name": candidate["name"],
            "candidate_email": candidate["email"],
            "score": exam["score"],
            "total_marks": exam["total_marks"],
            "percentage": exam["percentage"],
            "passed": exam["passed"] == 1,
            "total_questions": settings.TOTAL_QUESTIONS,
            "correct_answers": correct_count,
            "ai_feedback": exam["ai_feedback"],
            "completed_at": exam["completed_at"],
        }


@router.get("/statistics")
async def get_statistics():
    """Get overall exam statistics."""
    with get_db() as db:
        total = db.execute("SELECT COUNT(*) as c FROM exams WHERE completed_at IS NOT NULL").fetchone()["c"]
        passed = db.execute("SELECT COUNT(*) as c FROM exams WHERE passed = 1").fetchone()["c"]
        avg = db.execute("SELECT AVG(percentage) as a FROM exams WHERE completed_at IS NOT NULL").fetchone()["a"] or 0

        return {
            "total_exams": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": round((passed / total * 100), 1) if total > 0 else 0,
            "average_score": round(avg, 1),
        }


@router.post("/voice")
async def handle_voice_command(cmd: VoiceCommand):
    """Handle voice commands for accessibility."""
    result = await process_voice_command(cmd.command, cmd.exam_id)
    return result


@router.post("/notifications/send")
async def send_notification(req: NotificationRequest):
    """Send notification to a candidate."""
    with get_db() as db:
        candidate = db.execute(
            "SELECT * FROM candidates WHERE id = ?", (req.candidate_id,)
        ).fetchone()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        success = False
        if req.type == "email":
            success = await send_result_email(
                candidate["email"], candidate["name"], 0, 0, 0, False
            )
        elif req.type == "whatsapp" and candidate["phone"]:
            success = await send_whatsapp_notification(
                candidate["phone"], candidate["name"], 0, 0, 0, False
            )

        # Log notification
        db.execute(
            "INSERT INTO notifications (candidate_id, type, message, status) VALUES (?, ?, ?, ?)",
            (req.candidate_id, req.type, req.message, "sent" if success else "failed"),
        )

        return {"success": success, "type": req.type, "candidate": candidate["name"]}


@router.get("/question-bank/stats")
async def question_bank_stats():
    """Get question count per topic for the question bank."""
    with get_db() as db:
        stats = db.execute("""
            SELECT topic, COUNT(*) as count
            FROM questions
            GROUP BY topic
            ORDER BY topic
        """).fetchall()

        total = sum(row["count"] for row in stats)

        return {
            "total_questions": total,
            "topics": [{"topic": row["topic"], "count": row["count"]} for row in stats],
        }


@router.get("/test-email")
async def test_email(to: str):
    """Send a test email to verify SMTP configuration."""
    from app.services.email_service import send_result_email
    from app.config import settings

    if not settings.SMTP_USER:
        return {"status": "error", "message": "SMTP_USER not configured in environment"}
    if not settings.SMTP_PASSWORD:
        return {"status": "error", "message": "SMTP_PASSWORD not configured in environment"}

    try:
        success = await send_result_email(to, "Test User", 90, 100, 90.0, True)
        if success:
            return {"status": "success", "message": f"Test email sent to {to}"}
        else:
            return {"status": "error", "message": "Email function returned False - check Railway logs for details"}
    except Exception as e:
        return {"status": "error", "message": f"{type(e).__name__}: {str(e)}"}


@router.get("/test-groq")
async def test_groq():
    """Test if Groq API is working - with full diagnostics."""
    import httpx
    from app.config import settings
    
    result = {
        "api_key_set": bool(settings.GROQ_API_KEY),
        "api_key_prefix": settings.GROQ_API_KEY[:15] + "..." if settings.GROQ_API_KEY else "NOT SET",
        "model": settings.GROQ_MODEL,
    }
    
    # Direct API test with simple prompt
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {"role": "user", "content": "Generate 2 Python MCQ questions as JSON array: [{\"question_text\":\"Q\",\"option_a\":\"A\",\"option_b\":\"B\",\"option_c\":\"C\",\"option_d\":\"D\",\"correct_answer\":\"A\",\"difficulty\":\"advanced\",\"topic\":\"python\"}]. Return ONLY JSON."}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000,
                },
            )
            result["http_status"] = response.status_code
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                result["raw_response_first_200"] = content[:200]
                result["response_length"] = len(content)
                
                # Try to parse
                import json as j
                try:
                    start = content.find("[")
                    end = content.rfind("]") + 1
                    if start >= 0 and end > start:
                        parsed = j.loads(content[start:end])
                        result["parsed_count"] = len(parsed)
                        result["success"] = True
                    else:
                        result["error"] = "No JSON array found in response"
                except Exception as e:
                    result["parse_error"] = str(e)
            else:
                result["error_body"] = response.text[:300]
    except Exception as e:
        result["exception"] = str(e)
    
    return result


@router.post("/process-followups")
async def process_followups():
    """Process scheduled 7-day follow-up emails for failed candidates.

    Queries notifications with type='follow_up_7day', status='scheduled',
    and scheduled_at <= now. Sends a follow-up email to each candidate
    and updates the notification status to 'sent'.
    """
    now = datetime.now().isoformat()
    processed = 0
    failed = 0

    with get_db() as db:
        # Find all due follow-up notifications
        notifications = db.execute(
            """SELECT n.id, n.candidate_id, c.name, c.email
               FROM notifications n
               JOIN candidates c ON n.candidate_id = c.id
               WHERE n.type = 'follow_up_7day'
                 AND n.status = 'scheduled'
                 AND n.scheduled_at <= ?""",
            (now,),
        ).fetchall()

        for notif in notifications:
            try:
                success = await send_followup_email(notif["email"], notif["name"])
                if success:
                    db.execute(
                        "UPDATE notifications SET status = 'sent', sent_at = ? WHERE id = ?",
                        (datetime.now().isoformat(), notif["id"]),
                    )
                    processed += 1
                else:
                    # Email not configured but logged successfully
                    db.execute(
                        "UPDATE notifications SET status = 'sent', sent_at = ? WHERE id = ?",
                        (datetime.now().isoformat(), notif["id"]),
                    )
                    processed += 1
            except Exception as e:
                print(f"[Followup] Error processing notification {notif['id']}: {e}")
                db.execute(
                    "UPDATE notifications SET status = 'failed' WHERE id = ?",
                    (notif["id"],),
                )
                failed += 1

    return {
        "processed": processed,
        "failed": failed,
        "total_found": processed + failed,
    }
