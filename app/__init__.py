"""
Career Lab Consulting - Python Evaluation System
Application factory
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from app.database import init_db
from app.config import settings
from app.routers import exam, admin, auth, api

# Resolve paths relative to this file's location for reliable path resolution
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler: initialize database on startup."""
    init_db()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="Career Lab Consulting - Python Evaluation System",
        description="AI-powered Python evaluation platform with Groq AI integration",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Add session middleware for admin authentication
    application.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

    # Mount static files using absolute path
    application.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    # Include routers FIRST (so health check works immediately)
    application.include_router(auth.router)
    application.include_router(exam.router)
    application.include_router(admin.router)
    application.include_router(api.router)

    return application
