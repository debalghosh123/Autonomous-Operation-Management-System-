"""
Career Lab Consulting - Voice Mode Service
Voice command processing for accessibility
"""
from app.services.groq_service import generate_voice_response


async def process_voice_command(command: str, exam_id: int = None) -> dict:
    """Process voice commands for exam interaction."""
    command_lower = command.lower().strip()

    # Built-in commands
    if "next" in command_lower or "skip" in command_lower:
        return {
            "action": "next_question",
            "message": "Moving to the next question.",
            "success": True,
        }
    elif "previous" in command_lower or "back" in command_lower:
        return {
            "action": "previous_question",
            "message": "Going back to the previous question.",
            "success": True,
        }
    elif "submit" in command_lower or "finish" in command_lower:
        return {
            "action": "submit_exam",
            "message": "Submitting your exam now.",
            "success": True,
        }
    elif command_lower.startswith("select ") or command_lower.startswith("answer "):
        # Extract option
        for opt in ["a", "b", "c", "d"]:
            if opt in command_lower.split()[-1].lower():
                return {
                    "action": "select_answer",
                    "answer": opt.upper(),
                    "message": f"Selected option {opt.upper()}.",
                    "success": True,
                }
        return {
            "action": "error",
            "message": "Please say 'select A', 'select B', 'select C', or 'select D'.",
            "success": False,
        }
    elif "time" in command_lower:
        return {
            "action": "show_time",
            "message": "Showing remaining time.",
            "success": True,
        }
    elif "help" in command_lower:
        return {
            "action": "help",
            "message": "Available commands: next, previous, select A/B/C/D, submit, time, help.",
            "success": True,
        }
    else:
        # Use AI for unknown commands
        ai_response = await generate_voice_response(command)
        return {
            "action": "ai_response",
            "message": ai_response,
            "success": True,
        }
