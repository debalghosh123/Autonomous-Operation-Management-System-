"""
Career Lab Consulting - Python Evaluation System
Main application entry point
"""
import os
import uvicorn
from app import create_app
from app.config import settings

app = create_app()

# Startup diagnostics
print("=" * 50)
print("Career Lab Consulting - Python Evaluation System")
print("=" * 50)
print(f"GROQ_API_KEY loaded: {'YES (' + settings.GROQ_API_KEY[:10] + '...)' if settings.GROQ_API_KEY else 'NO - AI QUESTIONS WILL NOT WORK!'}")
print(f"GROQ_MODEL: {settings.GROQ_MODEL}")
print(f"PORT: {os.getenv('PORT', '8000')}")
if settings.SECRET_KEY == "career-lab-secret-key-change-in-production":
    print("WARNING: Using default SECRET_KEY - set SECRET_KEY env var in production!")
print("=" * 50)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
