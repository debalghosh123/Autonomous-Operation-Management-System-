"""
Career Lab Consulting - Groq AI Service
AI-powered question generation, feedback and evaluation using Groq API
"""
import os
import json
import httpx
from app.config import settings


async def generate_ai_questions(num_questions: int = 25) -> list:
    """Generate difficult Python questions using Groq AI (llama3)."""
    if not settings.GROQ_API_KEY:
        print("[GROQ] No API key configured - using fallback questions")
        return []
    
    print(f"[GROQ] Generating {num_questions} questions using model: {settings.GROQ_MODEL}")

    prompt = f"""Generate {num_questions} advanced Python MCQ questions as a JSON array.
Each question must test DEEP knowledge: metaclasses, GIL, descriptors, asyncio, memory, decorators.

Format - return ONLY this JSON array, nothing else:
[{{"question_text":"question here","option_a":"A answer","option_b":"B answer","option_c":"C answer","option_d":"D answer","correct_answer":"B","difficulty":"advanced","topic":"decorators"}}]

Rules:
- {num_questions} questions total
- Include Python code in questions
- Make them TRICKY - test deep understanding
- correct_answer must be A, B, C, or D
- Return ONLY valid JSON array"""

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": "You generate Python MCQ questions. Respond with ONLY a valid JSON array. No explanation."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.9,
                    "max_tokens": 8000,
                },
            )
            print(f"[GROQ] API response status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()
                print(f"[GROQ] Response length: {len(content)} chars")
                # Extract JSON from response
                if "```" in content:
                    parts = content.split("```")
                    for part in parts:
                        if part.strip().startswith("json"):
                            content = part.strip()[4:].strip()
                            break
                        elif part.strip().startswith("["):
                            content = part.strip()
                            break
                start = content.find("[")
                end = content.rfind("]") + 1
                if start != -1 and end > start:
                    content = content[start:end]
                questions = json.loads(content)
                # Validate questions
                valid_questions = []
                for q in questions[:num_questions]:
                    if all(k in q for k in ["question_text", "option_a", "option_b", "option_c", "option_d", "correct_answer"]):
                        q.setdefault("difficulty", "advanced")
                        q.setdefault("topic", "python")
                        q.setdefault("marks", 4)
                        valid_questions.append(q)
                print(f"[GROQ] Valid questions: {len(valid_questions)}")
                return valid_questions
            else:
                print(f"[GROQ] API error: {response.status_code} - {response.text[:200]}")
    except Exception as e:
        print(f"[GROQ] Exception: {e}")
        import traceback
        traceback.print_exc()
    
    return []

async def generate_ai_feedback(score: int, total_marks: int, percentage: float,
                                topic_performance: dict) -> str:
    """Generate AI-powered feedback using Groq API."""
    if not settings.GROQ_API_KEY:
        return _generate_fallback_feedback(score, total_marks, percentage, topic_performance)

    prompt = f"""You are a senior Python engineering mentor at Career Lab Consulting, an elite AI consulting firm in Gurugram, India.

A candidate just completed their Python evaluation exam. Analyze their performance RUTHLESSLY but CONSTRUCTIVELY.

Results:
- Score: {score}/{total_marks}
- Percentage: {percentage:.1f}%
- Pass/Fail: {"PASSED - QUALIFIED" if percentage >= 90 else "FAILED - NOT QUALIFIED"} (90% required)
- Topic Performance: {json.dumps(topic_performance, indent=2)}

Provide a DETAILED, PRODUCTION-FOCUSED evaluation report:

## PERFORMANCE VERDICT
Give a 2-3 sentence brutally honest assessment. Are they production-ready?

## CRITICAL LOOPHOLES IDENTIFIED
- Pinpoint exact technical gaps that would BREAK production systems
- Be specific: "Your understanding of X is shallow because..."
- Identify dangerous misconceptions

## SUBJECTS TO BRUSH UP (Priority Order)
For EACH weak area, provide:
1. The topic name
2. WHY it matters in production
3. Specific concepts to master
4. Recommended resources (books/courses)

## PRODUCTION READINESS SCORE
Rate them: Junior/Mid/Senior/Not Ready
Explain what level they'd function at in a real Python team.

## 2-WEEK INTENSIVE STUDY PLAN
Day-by-day plan to fix their gaps:
- Week 1: Fundamentals they're missing
- Week 2: Advanced topics & real-world practice

## MOTIVATIONAL CLOSE
End with honest encouragement. Tell them exactly what stands between them and production-readiness.

Keep it professional, specific, and actionable. No generic advice. This feedback should TRANSFORM their learning path."""

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
                    "max_tokens": 4096,
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
