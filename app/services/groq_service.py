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
        print("[GROQ] No API key - fallback")
        return []

    print(f"[GROQ] Generating {num_questions} Qs, model: {settings.GROQ_MODEL}")

    prompt = f"""Generate {num_questions} advanced Python MCQ questions as JSON array.
Each tests DEEP knowledge: metaclasses, GIL, descriptors, asyncio, memory, decorators.
Return ONLY valid JSON: [{{"question_text":"Q","option_a":"A","option_b":"B","option_c":"C","option_d":"D","correct_answer":"B","difficulty":"advanced","topic":"topic"}}]
Make them TRICKY. Include code snippets. {num_questions} questions. ONLY JSON array."""

    models_to_try = ["llama-3.1-8b-instant", "gemma2-9b-it", "llama3-70b-8192", "llama-3.3-70b-versatile"]

    for model in models_to_try:
        try:
            print(f"[GROQ] Trying model: {model}")
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": "Return ONLY valid JSON array. No text."},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.9,
                        "max_tokens": 8000,
                    },
                )
                print(f"[GROQ] Status: {response.status_code}")

                if response.status_code != 200:
                    print(f"[GROQ] Error: {response.text[:300]}")
                    continue

                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()
                print(f"[GROQ] Got {len(content)} chars")

                # Parse JSON
                if "```" in content:
                    for part in content.split("```"):
                        p = part.strip()
                        if p.startswith("json"):
                            content = p[4:].strip()
                            break
                        elif p.startswith("["):
                            content = p
                            break

                start = content.find("[")
                end = content.rfind("]") + 1
                if start >= 0 and end > start:
                    content = content[start:end]

                questions = json.loads(content)
                valid = []
                for q in questions[:num_questions]:
                    if "question" in str(q).lower() and len(q) >= 4:
                        q.setdefault("difficulty", "advanced")
                        q.setdefault("topic", "python")
                        q.setdefault("marks", 4)
                        valid.append(q)

                if valid:
                    print(f"[GROQ] SUCCESS: {len(valid)} questions generated")
                    return valid
                else:
                    print(f"[GROQ] Parsed 0 valid questions from response")

        except Exception as e:
            print(f"[GROQ] Exception with {model}: {e}")

    print("[GROQ] ALL MODELS FAILED")
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
        async with httpx.AsyncClient(timeout=12.0) as client:
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
    """Generate enterprise-grade evaluation feedback report."""

    # Determine production readiness level
    if percentage >= 90:
        readiness = "Senior Developer"
        verdict = "QUALIFIED - Production Ready"
    elif percentage >= 75:
        readiness = "Mid-Level Developer"
        verdict = "NOT QUALIFIED - Close to Target"
    elif percentage >= 50:
        readiness = "Junior Developer"
        verdict = "NOT QUALIFIED - Significant Gaps"
    elif percentage >= 30:
        readiness = "Trainee Level"
        verdict = "NOT QUALIFIED - Major Development Needed"
    else:
        readiness = "Not Production Ready"
        verdict = "NOT QUALIFIED - Fundamental Gaps"

    # Topic study mapping
    study_guide = {
        "ai_agent_patterns": "ReAct framework, tool use patterns, LangChain chains, Pydantic validation, memory systems, prompt engineering",
        "functions_scope": "Decorators, closures, generators, *args/**kwargs, lambda functions, higher-order functions",
        "apis_requests": "REST API design, authentication (OAuth, API keys), error handling, rate limiting, pagination",
        "oop_advanced": "Design patterns (Factory, Observer, Strategy), metaclasses, abstract classes, SOLID principles",
        "async_programming": "asyncio event loop, coroutines, aiohttp, concurrent.futures, async generators",
        "file_io_errors": "Context managers, custom exceptions, logging, file streaming, JSON/CSV processing",
        "oop_basics": "Class design, __init__, inheritance, encapsulation, composition vs inheritance",
        "dictionaries_json": "Nested data manipulation, JSON schema validation, defaultdict, API response parsing",
        "pandas": "DataFrame operations, groupby, merge/join, pivot tables, data cleaning pipelines",
        "web_scraping": "BeautifulSoup selectors, pagination handling, data extraction patterns, ethical scraping",
        "lists_tuples_sets": "List comprehensions, set operations, tuple unpacking, deque, performance",
        "control_flow": "Pattern matching, guard clauses, state machines, decision trees",
        "loops": "Generator expressions, itertools, enumerate patterns, lazy evaluation",
        "variables_datatypes": "Type hints, dataclasses, enums, type coercion, memory model",
        "strings": "Regex patterns, text processing pipelines, encoding, template engines",
        "regex": "Named groups, lookahead/lookbehind, text extraction, URL/email parsing",
        "modules_packages": "Package architecture, __init__.py, relative imports, namespace packages",
        "python_setup": "Virtual environments, dependency management, project structure",
    }

    # Categorize topics
    strengths = []
    weaknesses = []
    for topic, data in sorted(topic_performance.items(), key=lambda x: -x[1].get("percentage", 0)):
        pct = data.get("percentage", 0)
        if pct >= 75:
            strengths.append((topic, data))
        else:
            weaknesses.append((topic, data))

    # Build report
    report = f"""
{'=' * 55}
  CAREER LAB CONSULTING - EVALUATION REPORT
{'=' * 55}

EXECUTIVE SUMMARY
{'-' * 55}
Score: {score}/{total_marks} ({percentage:.1f}%)
Status: {verdict}
Production Readiness: {readiness}
Questions Attempted: {sum(d.get('total', 0) for d in topic_performance.values())}
Correct Answers: {sum(d.get('correct', 0) for d in topic_performance.values())}
Passing Threshold: 90%


CORE COMPETENCIES ASSESSMENT
{'-' * 55}
"""
    for topic, data in sorted(topic_performance.items(), key=lambda x: -x[1].get("percentage", 0)):
        pct = data.get("percentage", 0)
        correct = data.get("correct", 0)
        total = data.get("total", 0)
        if pct >= 90:
            level = "EXPERT"
        elif pct >= 75:
            level = "PROFICIENT"
        elif pct >= 50:
            level = "DEVELOPING"
        else:
            level = "NEEDS IMPROVEMENT"
        topic_name = topic.replace('_', ' ').title()
        report += f"  {topic_name}: {correct}/{total} ({pct:.0f}%) - {level}\n"

    if strengths:
        report += f"""

STRENGTHS IDENTIFIED
{'-' * 55}
"""
        for topic, data in strengths:
            topic_name = topic.replace('_', ' ').title()
            pct = data.get("percentage", 0)
            report += f"  + {topic_name} ({pct:.0f}%)\n"
            report += f"    Strong foundation in: {study_guide.get(topic, 'General Python')}\n\n"

    if weaknesses:
        report += f"""
AREAS FOR IMPROVEMENT
{'-' * 55}
"""
        for topic, data in weaknesses:
            topic_name = topic.replace('_', ' ').title()
            pct = data.get("percentage", 0)
            correct = data.get("correct", 0)
            total = data.get("total", 0)
            report += f"  - {topic_name}: {correct}/{total} ({pct:.0f}%)\n"
            report += f"    Must study: {study_guide.get(topic, 'Review fundamentals')}\n\n"

        report += f"""
DETAILED STUDY PLAN
{'-' * 55}
"""
        for i, (topic, data) in enumerate(weaknesses, 1):
            topic_name = topic.replace('_', ' ').title()
            pct = data.get("percentage", 0)
            guide = study_guide.get(topic, "Review core concepts")
            report += f"  Priority {i}: {topic_name}\n"
            report += f"  Current Level: {pct:.0f}% | Target: 90%+\n"
            report += f"  Key Concepts: {guide}\n"
            if pct < 30:
                report += f"  Approach: Start from basics, work through tutorials, build mini-projects\n"
            elif pct < 60:
                report += f"  Approach: Practice with coding challenges, implement real-world scenarios\n"
            else:
                report += f"  Approach: Focus on edge cases, advanced patterns, production best practices\n"
            report += "\n"

    report += f"""
14-DAY IMPROVEMENT ROADMAP
{'-' * 55}
  Week 1 (Days 1-7): Foundation Building
    - Days 1-2: Review weakest topics (concepts + documentation)
    - Days 3-4: Hands-on coding exercises for each weak area
    - Days 5-7: Build a mini-project combining 2-3 weak topics

  Week 2 (Days 8-14): Advanced Practice
    - Days 8-9: Timed practice problems (simulate exam conditions)
    - Days 10-11: Build an AI agent using Python (end-to-end)
    - Days 12-13: Code review and optimization of your projects
    - Day 14: Mock exam attempt before official reattempt


NEXT STEPS
{'-' * 55}
"""
    if percentage >= 90:
        report += """  Congratulations! You have QUALIFIED.
  Our team will reach out to you shortly regarding the next stage.
  Welcome to Career Lab Consulting!
"""
    else:
        report += f"""  1. Review the study plan above carefully
  2. Focus on your {len(weaknesses)} weak area(s) first
  3. Practice daily for at least 2 hours
  4. You may reattempt the evaluation after 14 days
  5. A follow-up email will be sent in 7 days with additional guidance

  Remember: Every expert was once a beginner. Your dedication to
  improvement is what matters most. We believe in your potential.
"""

    report += f"""
{'=' * 55}
  Career Lab Consulting | Python Evaluation System
  Report generated automatically | Confidential
{'=' * 55}
"""
    return report


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
