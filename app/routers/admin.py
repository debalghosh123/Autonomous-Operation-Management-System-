"""
Career Lab Consulting - Admin Router
Admin dashboard and management panel
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.database import get_db
from app.config import settings

router = APIRouter(prefix="/admin", tags=["Admin"])
templates = Jinja2Templates(directory="templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Admin dashboard with statistics."""
    with get_db() as db:
        # Get statistics
        total_candidates = db.execute("SELECT COUNT(*) as count FROM candidates").fetchone()["count"]
        total_exams = db.execute("SELECT COUNT(*) as count FROM exams WHERE completed_at IS NOT NULL").fetchone()["count"]
        passed_exams = db.execute("SELECT COUNT(*) as count FROM exams WHERE passed = 1").fetchone()["count"]
        avg_score = db.execute("SELECT AVG(percentage) as avg FROM exams WHERE completed_at IS NOT NULL").fetchone()["avg"] or 0

        # Recent exams
        recent_exams = db.execute("""
            SELECT e.*, c.name, c.email
            FROM exams e JOIN candidates c ON e.candidate_id = c.id
            WHERE e.completed_at IS NOT NULL
            ORDER BY e.completed_at DESC LIMIT 20
        """).fetchall()

        # Recent logs
        recent_logs = db.execute(
            "SELECT * FROM admin_logs ORDER BY created_at DESC LIMIT 10"
        ).fetchall()

        return templates.TemplateResponse("admin/dashboard.html", {"request": request, 
                "total_candidates": total_candidates,
                "total_exams": total_exams,
                "passed_exams": passed_exams,
                "failed_exams": total_exams - passed_exams,
                "avg_score": round(avg_score, 1),
                "pass_rate": round((passed_exams / total_exams * 100), 1) if total_exams > 0 else 0,
                "recent_exams": [dict(e) for e in recent_exams],
                "recent_logs": [dict(l) for l in recent_logs],
            },
        )


@router.get("/candidates", response_class=HTMLResponse)
async def list_candidates(request: Request):
    """List all candidates."""
    with get_db() as db:
        candidates = db.execute("""
            SELECT c.*, 
                   COUNT(e.id) as exam_count,
                   MAX(e.percentage) as best_score
            FROM candidates c
            LEFT JOIN exams e ON c.id = e.candidate_id AND e.completed_at IS NOT NULL
            GROUP BY c.id
            ORDER BY c.registered_at DESC
        """).fetchall()

        return templates.TemplateResponse("admin/candidates.html", {"request": request, "candidates": [dict(c) for c in candidates]},
        )


@router.get("/questions", response_class=HTMLResponse)
async def manage_questions(request: Request, page: int = 1, topic: str = "", search: str = ""):
    """Question management page with pagination, topic filter, and search."""
    per_page = 50
    offset = (page - 1) * per_page

    with get_db() as db:
        # Build query with optional filters
        where_clauses = []
        params = []

        if topic:
            where_clauses.append("topic = ?")
            params.append(topic)

        if search:
            where_clauses.append("question_text LIKE ?")
            params.append(f"%{search}%")

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        # Get total count with filters
        count_query = f"SELECT COUNT(*) as count FROM questions {where_sql}"
        total_count = db.execute(count_query, params).fetchone()["count"]

        # Get paginated questions
        query = f"SELECT * FROM questions {where_sql} ORDER BY id LIMIT ? OFFSET ?"
        questions = db.execute(query, params + [per_page, offset]).fetchall()

        # Get all available topics for filter dropdown
        topics = db.execute(
            "SELECT DISTINCT topic FROM questions ORDER BY topic"
        ).fetchall()
        topic_list = [t["topic"] for t in topics]

        total_pages = (total_count + per_page - 1) // per_page

        return templates.TemplateResponse("admin/questions.html", {
            "request": request,
            "questions": [dict(q) for q in questions],
            "page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "per_page": per_page,
            "topics": topic_list,
            "current_topic": topic,
            "current_search": search,
        })


@router.get("/exam/{exam_id}", response_class=HTMLResponse)
async def view_exam_detail(request: Request, exam_id: int):
    """View detailed exam results."""
    with get_db() as db:
        exam = db.execute("SELECT * FROM exams WHERE id = ?", (exam_id,)).fetchone()
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")

        candidate = db.execute(
            "SELECT * FROM candidates WHERE id = ?", (exam["candidate_id"],)
        ).fetchone()

        answers = db.execute("""
            SELECT a.*, q.question_text, q.correct_answer, q.option_a, q.option_b, q.option_c, q.option_d, q.topic
            FROM answers a JOIN questions q ON a.question_id = q.id
            WHERE a.exam_id = ?
        """, (exam_id,)).fetchall()

        return templates.TemplateResponse("admin/exam_detail.html", {"request": request, 
                "exam": dict(exam),
                "candidate": dict(candidate),
                "answers": [dict(a) for a in answers],
            },
        )
