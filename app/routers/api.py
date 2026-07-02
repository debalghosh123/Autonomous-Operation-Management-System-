"""
Career Lab Consulting - API Router
RESTful API endpoints for programmatic access
"""
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
from app.services.email_service import send_result_email
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


@router.get("/test-groq")
async def test_groq():
    """Test if Groq API is working."""
    from app.services.groq_service import generate_ai_questions
    from app.config import settings
    
    result = {
        "api_key_set": bool(settings.GROQ_API_KEY),
        "api_key_prefix": settings.GROQ_API_KEY[:15] + "..." if settings.GROQ_API_KEY else "NOT SET",
        "model": settings.GROQ_MODEL,
    }
    
    # Try generating just 2 questions
    try:
        questions = await generate_ai_questions(2)
        result["questions_generated"] = len(questions)
        result["success"] = len(questions) > 0
        if questions:
            result["sample_question"] = questions[0]["question_text"][:100]
    except Exception as e:
        result["error"] = str(e)
        result["success"] = False
    
    return result
