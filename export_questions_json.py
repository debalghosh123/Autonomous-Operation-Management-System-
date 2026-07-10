"""
Export all 10 question bank Python files to a single JSON file for fast loading.

This avoids the expensive Python AST compilation of 5.1MB of list literals,
which causes Vercel serverless cold start timeouts.
"""
import json
import sys
import os
import importlib.util

# Load question bank modules directly (bypassing app/__init__.py which needs FastAPI)
project_root = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(project_root, "app")


def load_module_var(filename, varname):
    """Load a variable from a Python file without importing the full app package."""
    filepath = os.path.join(app_dir, filename)
    spec = importlib.util.spec_from_file_location(filename.replace(".py", ""), filepath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, varname)


print("Loading question banks...")
_q1 = load_module_var("question_bank.py", "QUESTION_BANK")
_q2 = load_module_var("question_bank_2.py", "QUESTIONS")
_q3 = load_module_var("question_bank_3.py", "QUESTIONS")
_q4 = load_module_var("question_bank_4.py", "QUESTIONS")
_q5 = load_module_var("question_bank_5.py", "QUESTIONS")
_q6 = load_module_var("question_bank_6.py", "QUESTIONS")
_q7 = load_module_var("question_bank_7.py", "QUESTIONS")
_q8 = load_module_var("question_bank_8.py", "QUESTIONS")
_q9 = load_module_var("question_bank_9.py", "QUESTIONS")
_q10 = load_module_var("question_bank_10.py", "QUESTIONS")

ALL_QUESTIONS = _q1 + _q2 + _q3 + _q4 + _q5 + _q6 + _q7 + _q8 + _q9 + _q10

output_path = os.path.join(app_dir, "questions.json")

with open(output_path, "w") as f:
    json.dump(ALL_QUESTIONS, f)

print(f"Exported {len(ALL_QUESTIONS)} questions to {output_path}")
print(f"File size: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")

# Verify answer distribution
from collections import Counter
answers = Counter(q["correct_answer"] for q in ALL_QUESTIONS)
print(f"Answer distribution: {dict(sorted(answers.items()))}")
