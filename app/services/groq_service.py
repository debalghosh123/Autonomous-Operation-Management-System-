"""
Career Lab Consulting - Groq AI Service
AI-powered feedback and evaluation using Groq API
"""
import os
import json
import httpx
from app.config import settings


async def generate_ai_feedback(score: int, total_marks: int, percentage: float,
                                topic_performance: dict) -> str:
    """Generate AI-powered feedback using Groq API."""
    if not settings.GROQ_API_KEY:
        return _generate_fallback_feedback(score, total_marks, percentage, topic_performance)

    prompt = f"""You are an expert Python programming evaluator for Career Lab Consulting.
A candidate just completed their Python evaluation exam.

Results:
- Score: {score}/{total_marks}
- Percentage: {percentage:.1f}%
- Pass/Fail: {"PASSED" if percentage >= 90 else "FAILED"} (90% required to qualify)
- Topic Performance: {json.dumps(topic_performance, indent=2)}

Please provide:
1. A brief performance summary (2-3 sentences)
2. Strengths identified (based on topics where they scored well)
3. Areas for improvement (based on topics where they scored poorly)
4. Specific study recommendations
5. An encouraging closing message

Keep the feedback professional, constructive, and actionable. Format it clearly."""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a professional Python programming evaluator."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1024,
                },
            )
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                return _generate_fallback_feedback(score, total_marks, percentage, topic_performance)
    except Exception:
        return _generate_fallback_feedback(score, total_marks, percentage, topic_performance)


def _generate_fallback_feedback(score: int, total_marks: int, percentage: float,
                                 topic_performance: dict) -> str:
    """Generate fallback feedback when AI is unavailable."""
    status = "PASSED" if percentage >= 90 else "FAILED"

    feedback = f"""
## Python Evaluation Results - Career Lab Consulting

### Performance Summary
You scored {score}/{total_marks} ({percentage:.1f}%). Status: {status}

### Topic-wise Performance
"""
    for topic, data in topic_performance.items():
        emoji = "+" if data.get("percentage", 0) >= 75 else "-"
        feedback += f"  {emoji} {topic.replace('_', ' ').title()}: {data.get('correct', 0)}/{data.get('total', 0)}\n"

    if percentage >= 90:
        feedback += "\n### Congratulations!\nYou have qualified the Python evaluation. Welcome to Career Lab Consulting!"
    else:
        feedback += "\n### Recommendations\nPlease review the topics where you scored below average and attempt again."

    return feedback


async def generate_voice_response(command: str) -> str:
    """Generate AI response for voice commands."""
    if not settings.GROQ_API_KEY:
        return f"Voice command received: {command}. AI service is not configured."

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a helpful exam assistant. Provide brief, helpful responses about the Python evaluation exam."},
                        {"role": "user", "content": command},
                    ],
                    "temperature": 0.5,
                    "max_tokens": 256,
                },
            )
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
    except Exception:
        pass

    return f"I received your command: '{command}'. Please try again or use the text interface."
