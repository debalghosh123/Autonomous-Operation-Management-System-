"""
Combined Question Bank - loads 10000 questions from JSON for fast serverless cold start.
"""
import json
import os

_dir = os.path.dirname(os.path.abspath(__file__))
_json_path = os.path.join(_dir, "questions.json")

with open(_json_path, "r") as f:
    ALL_QUESTIONS = json.load(f)

# Backwards-compatible alias used by app/routers/exam.py
QUESTION_BANK = ALL_QUESTIONS
