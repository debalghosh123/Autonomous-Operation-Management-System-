"""
Career Lab Consulting - Exam Router
Handles exam flow: start, questions, submit, results

NOTE: This module is designed to work on Vercel serverless where /tmp SQLite
is NOT shared between requests. The submit endpoint scores entirely from
form data (hidden fields) to avoid cross-request DB lookups.
"""
import os
import random
from fastapi import APIRouter, Request, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
from app.database import get_db
from app.config import settings
from app.services.groq_service import _generate_fallback_feedback
from app.services.email_service import send_result_email
from app.services.whatsapp_service import send_whatsapp_notification
from app.utils.helpers import calculate_percentage, is_passed
from app.question_bank_all import QUESTION_BANK


def _schedule_followup(candidate_id, candidate_name):
    """Schedule a 7-day follow-up notification for failed candidates."""
    try:
        follow_up_date = datetime.now() + timedelta(days=7)
        with get_db() as db:
            db.execute(
                """INSERT INTO notifications (candidate_id, type, message, status, scheduled_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    candidate_id,
                    "follow_up_7day",
                    f"Follow-up with {candidate_name} regarding next interview opportunity. Scheduled 7 days after exam attempt.",
                    "scheduled",
                    follow_up_date.isoformat(),
                ),
            )
        print(f"[Notification] Follow-up scheduled for {candidate_name}")
    except Exception as e:
        print(f"[Notification] Error scheduling follow-up: {e}")

router = APIRouter(prefix="/exam", tags=["Exam"])
_templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "templates")
templates = Jinja2Templates(directory=_templates_dir)


@router.get("/start/{candidate_id}", response_class=HTMLResponse)
async def start_exam(request: Request, candidate_id: int):
    """Start a new exam for a candidate."""
    with get_db() as db:
        candidate = db.execute(
            "SELECT * FROM candidates WHERE id = ?", (candidate_id,)
        ).fetchone()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # Check 14-day cooldown period
        last_exam = db.execute(
            "SELECT completed_at FROM exams WHERE candidate_id = ? AND completed_at IS NOT NULL ORDER BY completed_at DESC LIMIT 1",
            (candidate_id,)
        ).fetchone()

        if last_exam and last_exam["completed_at"]:
            completed_at = datetime.fromisoformat(last_exam["completed_at"])
            cooldown_end = completed_at + timedelta(days=14)
            now = datetime.now()
            if now < cooldown_end:
                retry_date = cooldown_end.strftime("%B %d, %Y")
                return templates.TemplateResponse("exam_start.html", {
                    "request": request,
                    "candidate": dict(candidate),
                    "cooldown_active": True,
                    "retry_date": retry_date,
                    "cooldown_message": f"You have already attempted the evaluation recently. You can retake the exam after {retry_date}.",
                })

        # Create new exam
        cursor = db.execute(
            "INSERT INTO exams (candidate_id, total_marks) VALUES (?, ?)",
            (candidate_id, settings.TOTAL_MARKS),
        )
        exam_id = cursor.lastrowid

        return templates.TemplateResponse("exam_start.html", {"request": request, 
                "candidate": dict(candidate),
                "exam_id": exam_id,
                "total_questions": settings.TOTAL_QUESTIONS,
                "marks_per_question": settings.MARKS_PER_QUESTION,
                "total_marks": settings.TOTAL_MARKS,
                "passing_percentage": settings.PASSING_PERCENTAGE,
                "duration": settings.EXAM_DURATION_MINUTES,
            },
        )


@router.get("/questions/{exam_id}", response_class=HTMLResponse)
async def get_questions(request: Request, exam_id: int):
    """Display exam questions - randomly selected from in-memory question bank.
    
    Uses Python's random.sample on the in-memory QUESTION_BANK to avoid
    relying on SQLite DB which is not shared across serverless invocations.
    """
    with get_db() as db:
        exam = db.execute("SELECT * FROM exams WHERE id = ?", (exam_id,)).fetchone()
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")

        candidate = db.execute(
            "SELECT * FROM candidates WHERE id = ?", (exam["candidate_id"],)
        ).fetchone()

    # Randomly select questions from in-memory question bank (no DB needed)
    num_questions = min(settings.TOTAL_QUESTIONS, len(QUESTION_BANK))
    questions = random.sample(QUESTION_BANK, num_questions)

    # Ensure each question has a marks field (default to MARKS_PER_QUESTION)
    for q in questions:
        if "marks" not in q:
            q["marks"] = settings.MARKS_PER_QUESTION

    return templates.TemplateResponse("exam_questions.html", {"request": request,
            "exam_id": exam_id,
            "candidate": dict(candidate),
            "questions": questions,
            "total_questions": len(questions),
            "duration": settings.EXAM_DURATION_MINUTES,
        },
    )


@router.post("/submit")
async def submit_exam(request: Request, background_tasks: BackgroundTasks):
    """Submit exam answers and calculate results.
    
    Scores entirely from form data (hidden fields) to work on serverless
    where /tmp SQLite is not shared between requests. No DB lookup needed.
    """
    form_data = await request.form()

    # Read candidate info and question data from hidden form fields
    total_questions = int(form_data.get("total_questions", 0))
    candidate_name = form_data.get("candidate_name", "")
    candidate_email = form_data.get("candidate_email", "")
    candidate_phone = form_data.get("candidate_phone", "")

    score = 0
    topic_performance = {}
    answers = []

    for i in range(1, total_questions + 1):
        correct_answer = form_data.get(f"correct_{i}", "")
        topic = form_data.get(f"topic_{i}", "python")
        marks = int(form_data.get(f"marks_{i}", settings.MARKS_PER_QUESTION))
        selected = form_data.get(f"question_{i}", "")

        is_correct = 1 if selected.upper() == correct_answer.upper() else 0

        if is_correct:
            score += marks

        if topic not in topic_performance:
            topic_performance[topic] = {"correct": 0, "total": 0, "percentage": 0}
        topic_performance[topic]["total"] += 1
        if is_correct:
            topic_performance[topic]["correct"] += 1

        answers.append({
            "selected_answer": selected,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "topic": topic,
        })

    # Calculate percentages for topics
    for topic in topic_performance:
        t = topic_performance[topic]
        t["percentage"] = round((t["correct"] / t["total"]) * 100, 1) if t["total"] > 0 else 0

    percentage = calculate_percentage(score, settings.TOTAL_MARKS)
    passed = is_passed(percentage, settings.PASSING_PERCENTAGE)

    # Generate feedback
    ai_feedback = _generate_fallback_feedback(score, settings.TOTAL_MARKS, percentage, topic_performance)

    # Try to persist results in DB (best-effort, may fail on serverless)
    exam_id = None
    candidate_id = None
    try:
        with get_db() as db:
            # Look up or create candidate record
            candidate_row = db.execute(
                "SELECT id FROM candidates WHERE email = ?", (candidate_email,)
            ).fetchone()
            candidate_id = candidate_row["id"] if candidate_row else None

            if candidate_id:
                # Update or create exam record
                cursor = db.execute(
                    """INSERT INTO exams (candidate_id, total_marks, completed_at, score, percentage, passed, ai_feedback)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (candidate_id, settings.TOTAL_MARKS, datetime.now().isoformat(),
                     score, percentage, 1 if passed else 0, ai_feedback),
                )
                exam_id = cursor.lastrowid

                # Log action
                db.execute(
                    "INSERT INTO admin_logs (action, details) VALUES (?, ?)",
                    ("exam_completed", f"Candidate {candidate_name} scored {score}/{settings.TOTAL_MARKS} ({percentage}%)"),
                )
    except Exception as e:
        print(f"[Exam] DB persistence failed (serverless expected): {e}")

    # Schedule follow-up for failed candidates (outside DB context to avoid lock)
    if not passed and candidate_id:
        _schedule_followup(candidate_id, candidate_name)

    # Schedule email notification via BackgroundTasks
    background_tasks.add_task(
        send_result_email, candidate_email, candidate_name,
        score, settings.TOTAL_MARKS, percentage, passed
    )

    if candidate_phone:
        background_tasks.add_task(
            send_whatsapp_notification, candidate_phone, candidate_name,
            score, settings.TOTAL_MARKS, percentage, passed
        )

    # Build exam dict for the result template
    exam_data = {
        "id": exam_id,
        "score": score,
        "total_marks": settings.TOTAL_MARKS,
        "percentage": percentage,
        "passed": 1 if passed else 0,
        "ai_feedback": ai_feedback,
        "completed_at": datetime.now().isoformat(),
    }

    candidate_data = {
        "name": candidate_name,
        "email": candidate_email,
        "phone": candidate_phone,
    }

    # Render result page directly (no redirect, no DB lookup needed)
    return templates.TemplateResponse("exam_result.html", {
        "request": request,
        "exam": exam_data,
        "candidate": candidate_data,
        "answers": answers,
        "passed": passed,
        "passing_percentage": settings.PASSING_PERCENTAGE,
        "topic_performance": topic_performance,
    })


@router.post("/submit/{exam_id}")
async def submit_exam_legacy(request: Request, exam_id: int, background_tasks: BackgroundTasks):
    """Legacy submit endpoint that redirects to the new /exam/submit handler.
    Kept for backwards compatibility with any cached forms."""
    return await submit_exam(request, background_tasks)


@router.get("/result/{exam_id}", response_class=HTMLResponse)
async def exam_result(request: Request, exam_id: int):
    """Display exam results with AI feedback."""
    with get_db() as db:
        exam = db.execute("SELECT * FROM exams WHERE id = ?", (exam_id,)).fetchone()
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")

        candidate = db.execute(
            "SELECT * FROM candidates WHERE id = ?", (exam["candidate_id"],)
        ).fetchone()

        # Try to get answers joined with ai_questions (used for randomly selected exams)
        answers = db.execute(
            """SELECT a.*, aq.question_text, aq.correct_answer, aq.topic
               FROM answers a
               JOIN ai_questions aq ON a.exam_id = aq.exam_id AND a.question_id = aq.question_number
               WHERE a.exam_id = ?
               ORDER BY aq.question_number""",
            (exam_id,),
        ).fetchall()

        # Fallback to legacy questions table join if no ai_questions found
        if not answers:
            answers = db.execute(
                """SELECT a.*, q.question_text, q.correct_answer, q.topic
                   FROM answers a JOIN questions q ON a.question_id = q.id
                   WHERE a.exam_id = ?""",
                (exam_id,),
            ).fetchall()

        # Calculate topic performance from answers
        topic_performance = {}
        for ans in answers:
            topic = ans["topic"] if ans["topic"] else "python"
            if topic not in topic_performance:
                topic_performance[topic] = {"correct": 0, "total": 0, "percentage": 0}
            topic_performance[topic]["total"] += 1
            if ans["is_correct"]:
                topic_performance[topic]["correct"] += 1

        for topic in topic_performance:
            t = topic_performance[topic]
            t["percentage"] = round((t["correct"] / t["total"]) * 100, 1) if t["total"] > 0 else 0

        return templates.TemplateResponse("exam_result.html", {"request": request, 
                "exam": dict(exam),
                "candidate": dict(candidate),
                "answers": [dict(a) for a in answers],
                "passed": exam["passed"] == 1,
                "passing_percentage": settings.PASSING_PERCENTAGE,
                "topic_performance": topic_performance,
            },
        )
