"""
Career Lab Consulting - Database Management
SQLite database initialization and session management
"""
import sqlite3
import os
from contextlib import contextmanager

DATABASE_PATH = os.getenv("DATABASE_PATH", "/tmp/evaluation.db")


def get_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    """Context manager for database sessions."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize the database with required tables."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            score INTEGER DEFAULT 0,
            total_marks INTEGER DEFAULT 100,
            percentage REAL DEFAULT 0.0,
            passed INTEGER DEFAULT 0,
            ai_feedback TEXT,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id)
        );

        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            difficulty TEXT DEFAULT 'advanced',
            topic TEXT DEFAULT 'general',
            marks INTEGER DEFAULT 4
        );

        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            selected_answer TEXT,
            is_correct INTEGER DEFAULT 0,
            answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (exam_id) REFERENCES exams(id),
            FOREIGN KEY (question_id) REFERENCES questions(id)
        );

        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS ai_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            question_number INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            difficulty TEXT DEFAULT 'advanced',
            topic TEXT DEFAULT 'python',
            marks INTEGER DEFAULT 4,
            FOREIGN KEY (exam_id) REFERENCES exams(id)
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            message TEXT NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (candidate_id) REFERENCES candidates(id)
        );
    """)

    # Seed questions if table is empty
    cursor.execute("SELECT COUNT(*) FROM questions")
    count = cursor.fetchone()[0]
    if count == 0:
        _seed_questions(cursor)

    conn.commit()
    conn.close()


def _seed_questions(cursor):
    """Seed the database with 25 Python evaluation questions."""
    questions = [
        ("What is the output of print(type([])) in Python?",
         "<class 'list'>", "<class 'array'>", "<class 'tuple'>", "<class 'dict'>",
         "A", "advanced", "data_types"),
        ("Which keyword is used to define a function in Python?",
         "func", "def", "function", "define",
         "B", "advanced", "functions"),
        ("What is the output of print(2**3)?",
         "6", "8", "9", "5",
         "B", "advanced", "operators"),
        ("Which of the following is immutable in Python?",
         "List", "Dictionary", "Set", "Tuple",
         "D", "advanced", "data_types"),
        ("What does the 'self' keyword represent in a class?",
         "The class itself", "The instance of the class", "A global variable", "A static method",
         "B", "advanced", "oop"),
        ("What is the output of print('hello'[1:])?",
         "hello", "ello", "hllo", "h",
         "B", "advanced", "strings"),
        ("Which method is used to add an element to a list?",
         "add()", "insert()", "append()", "push()",
         "C", "advanced", "data_structures"),
        ("What is a decorator in Python?",
         "A comment", "A function that modifies another function", "A class attribute", "A loop construct",
         "B", "advanced", "decorators"),
        ("What is the difference between '==' and 'is' in Python?",
         "No difference", "'==' checks value, 'is' checks identity", "'is' checks value, '==' checks identity", "Both check identity",
         "B", "advanced", "operators"),
        ("Which module is used for regular expressions in Python?",
         "regex", "re", "regexp", "match",
         "B", "advanced", "modules"),
        ("What is a lambda function?",
         "A named function", "An anonymous function", "A recursive function", "A generator function",
         "B", "advanced", "functions"),
        ("What is the output of print(list(range(0, 10, 2)))?",
         "[0, 2, 4, 6, 8]", "[0, 2, 4, 6, 8, 10]", "[2, 4, 6, 8]", "[0, 1, 2, 3, 4]",
         "A", "advanced", "built_ins"),
        ("What does the 'yield' keyword do in Python?",
         "Stops a function", "Creates a generator", "Returns a value permanently", "Raises an exception",
         "B", "expert", "generators"),
        ("Which of the following is used for exception handling?",
         "try/except", "if/else", "for/while", "switch/case",
         "A", "advanced", "error_handling"),
        ("What is the purpose of __init__ method in a class?",
         "To destroy an object", "To initialize an object", "To inherit a class", "To create a static method",
         "B", "advanced", "oop"),
        ("What is list comprehension?",
         "A way to create lists using loops", "A concise way to create lists", "A method to sort lists", "A way to delete lists",
         "B", "advanced", "data_structures"),
        ("What is the Global Interpreter Lock (GIL)?",
         "A security feature", "A mutex for thread safety in CPython", "A file locking mechanism", "A database lock",
         "B", "expert", "advanced"),
        ("Which data structure uses FIFO principle?",
         "Stack", "Queue", "Tree", "Graph",
         "B", "advanced", "data_structures"),
        ("What is the difference between deep copy and shallow copy?",
         "No difference", "Deep copy creates independent copy, shallow copy shares references", "Shallow copy is faster", "Deep copy only works with lists",
         "B", "expert", "advanced"),
        ("What is PEP 8?",
         "A Python version", "A style guide for Python code", "A Python library", "A testing framework",
         "B", "advanced", "best_practices"),
        ("Which of the following is a valid way to open a file?",
         "open('file.txt', 'r')", "file.open('file.txt')", "read('file.txt')", "File('file.txt')",
         "A", "advanced", "file_handling"),
        ("What does the map() function do?",
         "Creates a dictionary", "Applies a function to all items in an iterable", "Maps keys to values", "Creates a list",
         "B", "advanced", "built_ins"),
        ("What is the purpose of virtual environments in Python?",
         "To run Python faster", "To isolate project dependencies", "To create virtual machines", "To encrypt code",
         "B", "advanced", "best_practices"),
        ("What is monkey patching in Python?",
         "A testing technique", "Dynamically modifying a module at runtime", "A design pattern", "A debugging tool",
         "B", "expert", "advanced"),
        ("Which of the following is NOT a valid Python data type?",
         "int", "float", "char", "complex",
         "C", "advanced", "data_types"),
    ]

    for q in questions:
        cursor.execute("""
            INSERT INTO questions (question_text, option_a, option_b, option_c, option_d,
                                   correct_answer, difficulty, topic, marks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 4)
        """, q)
