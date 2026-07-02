"""
Career Lab Consulting - Python Evaluation System
Application factory
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.database import init_db
from app.routers import exam, admin, auth, api


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="Career Lab Consulting - Python Evaluation System",
        description="AI-powered Python evaluation platform with Groq AI integration",
        version="1.0.0",
    )

    # Mount static files
    application.mount("/static", StaticFiles(directory="static"), name="static")

    # Initialize database
    init_db()

    # Include routers
    application.include_router(auth.router)
    application.include_router(exam.router)
    application.include_router(admin.router)
    application.include_router(api.router)

    return application
