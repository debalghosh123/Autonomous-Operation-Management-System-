"""
Career Lab Consulting - Authentication Router
Handles candidate registration and admin login
"""
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.database import get_db
from app.config import settings

router = APIRouter(tags=["Authentication"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Landing page with Career Lab branding."""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Candidate registration page."""
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
async def register_candidate(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
):
    """Register a new candidate."""
    with get_db() as db:
        try:
            cursor = db.execute(
                "INSERT INTO candidates (name, email, phone) VALUES (?, ?, ?)",
                (name, email, phone),
            )
            candidate_id = cursor.lastrowid
            db.execute(
                "INSERT INTO admin_logs (action, details) VALUES (?, ?)",
                ("registration", f"Candidate {name} ({email}) registered"),
            )
            return RedirectResponse(url=f"/exam/start/{candidate_id}", status_code=303)
        except Exception as e:
            if "UNIQUE constraint" in str(e):
                # Candidate already exists, find their ID
                row = db.execute(
                    "SELECT id FROM candidates WHERE email = ?", (email,)
                ).fetchone()
                if row:
                    return RedirectResponse(url=f"/exam/start/{row['id']}", status_code=303)
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "error": "Registration failed. Email may already exist."},
            )


@router.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Admin login page."""
    return templates.TemplateResponse("admin/login.html", {"request": request})


@router.post("/admin/login")
async def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    """Authenticate admin."""
    if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
        request.session["admin_authenticated"] = True
        return RedirectResponse(url="/admin/dashboard", status_code=303)
    return templates.TemplateResponse(
        "admin/login.html",
        {"request": request, "error": "Invalid credentials"},
    )


@router.get("/admin/logout")
async def admin_logout(request: Request):
    """Logout admin and clear session."""
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=303)
