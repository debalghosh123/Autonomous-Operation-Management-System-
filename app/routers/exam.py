"""
Career Lab Consulting - Exam Router
Handles exam flow: start, questions, submit, results
"""
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from app.database import get_db
from app.config import settings
from app.services.groq_service import generate_ai_feedback
from app.services.email_service import send_result_email
from app.services.whatsapp_service import send_whatsapp_notification
from app.utils.helpers import calculate_percentage, is_passed

router = APIRouter(prefix="/exam", tags=["Exam"])
templates = Jinja2Templates(directory="templates")


@router.get("/start/{candidate_id}", response_class=HTMLResponse)
async def start_exam(request: Request, candidate_id: int):
    """Start a new exam for a candidate."""
    with get_db() as db:
        candidate = db.execute(
            "SELECT * FROM candidates WHERE id = ?", (candidate_id,)
        ).fetchone()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

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
    """Display exam questions."""
    with get_db() as db:
        exam = db.execute("SELECT * FROM exams WHERE id = ?", (exam_id,)).fetchone()
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")

        candidate = db.execute(
            "SELECT * FROM candidates WHERE id = ?", (exam["candidate_id"],)
        ).fetchone()

        questions = db.execute(
            "SELECT id, question_text, option_a, option_b, option_c, option_d, difficulty, topic, marks FROM questions ORDER BY id LIMIT ?",
            (settings.TOTAL_QUESTIONS,),
        ).fetchall()

        return templates.TemplateResponse("exam_questions.html", {"request": request, 
                "exam_id": exam_id,
                "candidate": dict(candidate),
                "questions": [dict(q) for q in questions],
                "total_questions": len(questions),
                "duration": settings.EXAM_DURATION_MINUTES,
            },
        )


@router.post("/submit/{exam_id}")
async def submit_exam(request: Request, exam_id: int):
    """Submit exam answers and calculate results."""
    form_data = await request.form()

    with get_db() as db:
        exam = db.execute("SELECT * FROM exams WHERE id = ?", (exam_id,)).fetchone()
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")

        candidate = db.execute(
            "SELECT * FROM candidates WHERE id = ?", (exam["candidate_id"],)
        ).fetchone()

        questions = db.execute(
            "SELECT * FROM questions ORDER BY id LIMIT ?",
            (settings.TOTAL_QUESTIONS,),
        ).fetchall()

        score = 0
        topic_performance = {}

        for question in questions:
            q_id = str(question["id"])
            selected = form_data.get(f"question_{q_id}", "")
            is_correct = 1 if selected.upper() == question["correct_answer"].upper() else 0

            if is_correct:
                score += question["marks"]

            # Track topic performance
            topic = question["topic"]
            if topic not in topic_performance:
                topic_performance[topic] = {"correct": 0, "total": 0, "percentage": 0}
            topic_performance[topic]["total"] += 1
            if is_correct:
                topic_performance[topic]["correct"] += 1

            # Save answer
            db.execute(
                "INSERT INTO answers (exam_id, question_id, selected_answer, is_correct) VALUES (?, ?, ?, ?)",
                (exam_id, question["id"], selected, is_correct),
            )

        # Calculate percentages for topics
        for topic in topic_performance:
            t = topic_performance[topic]
            t["percentage"] = round((t["correct"] / t["total"]) * 100, 1) if t["total"] > 0 else 0

        percentage = calculate_percentage(score, settings.TOTAL_MARKS)
        passed = is_passed(percentage, settings.PASSING_PERCENTAGE)

        # Generate AI feedback
        ai_feedback = await generate_ai_feedback(score, settings.TOTAL_MARKS, percentage, topic_performance)

        # Update exam record
        db.execute(
            """UPDATE exams SET completed_at = ?, score = ?, percentage = ?,
               passed = ?, ai_feedback = ? WHERE id = ?""",
            (datetime.now().isoformat(), score, percentage, 1 if passed else 0, ai_feedback, exam_id),
        )

        # Log action
        db.execute(
            "INSERT INTO admin_logs (action, details) VALUES (?, ?)",
            ("exam_completed", f"Candidate {candidate['name']} scored {score}/{settings.TOTAL_MARKS} ({percentage}%)"),
        )

    # Send notifications (non-blocking)
    try:
        await send_result_email(
            candidate["email"], candidate["name"],
            score, settings.TOTAL_MARKS, percentage, passed
        )
    except Exception:
        pass

    if candidate["phone"]:
        try:
            await send_whatsapp_notification(
                candidate["phone"], candidate["name"],
                score, settings.TOTAL_MARKS, percentage, passed
            )
        except Exception:
            pass

    return RedirectResponse(url=f"/exam/result/{exam_id}", status_code=303)


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

        answers = db.execute(
            """SELECT a.*, q.question_text, q.correct_answer, q.topic
               FROM answers a JOIN questions q ON a.question_id = q.id
               WHERE a.exam_id = ?""",
            (exam_id,),
        ).fetchall()

        return templates.TemplateResponse("exam_result.html", {"request": request, 
                "exam": dict(exam),
                "candidate": dict(candidate),
                "answers": [dict(a) for a in answers],
                "passed": exam["passed"] == 1,
                "passing_percentage": settings.PASSING_PERCENTAGE,
            },
        )
