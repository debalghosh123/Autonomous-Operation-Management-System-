"""
Career Lab Consulting - Exam Router
Handles exam flow: start, questions, submit, results
"""
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
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
    """Display exam questions - randomly selected from 1000-question bank."""
    with get_db() as db:
        exam = db.execute("SELECT * FROM exams WHERE id = ?", (exam_id,)).fetchone()
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")

        candidate = db.execute(
            "SELECT * FROM candidates WHERE id = ?", (exam["candidate_id"],)
        ).fetchone()

        # Check if questions already exist for this exam (idempotency guard)
        existing = db.execute(
            "SELECT * FROM ai_questions WHERE exam_id = ? ORDER BY question_number",
            (exam_id,),
        ).fetchall()

        if existing:
            # Use previously selected questions (prevents duplication on refresh)
            questions = [dict(q) for q in existing]
        else:
            # Randomly select questions from the question bank
            rows = db.execute(
                """SELECT id, question_text, option_a, option_b, option_c, option_d,
                          correct_answer, difficulty, topic, marks
                   FROM questions ORDER BY RANDOM() LIMIT ?""",
                (settings.TOTAL_QUESTIONS,),
            ).fetchall()
            questions = [dict(q) for q in rows]

            # Store selected questions in ai_questions table for this exam (for scoring)
            for i, q in enumerate(questions):
                db.execute(
                    """INSERT INTO ai_questions (exam_id, question_number, question_text,
                       option_a, option_b, option_c, option_d, correct_answer, difficulty, topic, marks)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (exam_id, i + 1, q["question_text"], q["option_a"], q["option_b"],
                     q["option_c"], q["option_d"], q["correct_answer"],
                     q.get("difficulty", "advanced"), q.get("topic", "python"),
                     q.get("marks", 4)),
                )

    return templates.TemplateResponse("exam_questions.html", {"request": request,
            "exam_id": exam_id,
            "candidate": dict(candidate),
            "questions": questions,
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

        # Get the randomly selected questions stored for this exam
        ai_qs = db.execute(
            "SELECT * FROM ai_questions WHERE exam_id = ? ORDER BY question_number",
            (exam_id,)
        ).fetchall()

        score = 0
        topic_performance = {}

        if ai_qs:
            questions = [dict(q) for q in ai_qs]

            for i, question in enumerate(questions):
                q_num = str(i + 1)
                selected = form_data.get(f"question_{q_num}", "")
                is_correct = 1 if selected.upper() == question["correct_answer"].upper() else 0

                if is_correct:
                    score += question["marks"]

                topic = question.get("topic", "python")
                if topic not in topic_performance:
                    topic_performance[topic] = {"correct": 0, "total": 0, "percentage": 0}
                topic_performance[topic]["total"] += 1
                if is_correct:
                    topic_performance[topic]["correct"] += 1

                db.execute(
                    "INSERT INTO answers (exam_id, question_id, selected_answer, is_correct) VALUES (?, ?, ?, ?)",
                    (exam_id, question["question_number"], selected, is_correct),
                )
        else:
            # Fallback to database questions (legacy path)
            questions = db.execute(
                "SELECT * FROM questions ORDER BY id LIMIT ?",
                (settings.TOTAL_QUESTIONS,),
            ).fetchall()

            for i, question in enumerate(questions):
                q_num = str(i + 1)
                selected = form_data.get(f"question_{q_num}", "")
                is_correct = 1 if selected.upper() == question["correct_answer"].upper() else 0

                if is_correct:
                    score += question["marks"]

                topic = question["topic"]
                if topic not in topic_performance:
                    topic_performance[topic] = {"correct": 0, "total": 0, "percentage": 0}
                topic_performance[topic]["total"] += 1
                if is_correct:
                    topic_performance[topic]["correct"] += 1

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

    # Schedule 7-day follow-up notification for failed candidates
    if not passed:
        try:
            follow_up_date = datetime.now() + timedelta(days=7)
            with get_db() as db:
                db.execute(
                    """INSERT INTO notifications (candidate_id, type, message, status, scheduled_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        candidate["id"],
                        "follow_up_7day",
                        f"Follow-up with {candidate['name']} regarding next interview opportunity. Scheduled 7 days after exam attempt.",
                        "scheduled",
                        follow_up_date.isoformat(),
                    ),
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

        return templates.TemplateResponse("exam_result.html", {"request": request, 
                "exam": dict(exam),
                "candidate": dict(candidate),
                "answers": [dict(a) for a in answers],
                "passed": exam["passed"] == 1,
                "passing_percentage": settings.PASSING_PERCENTAGE,
            },
        )
