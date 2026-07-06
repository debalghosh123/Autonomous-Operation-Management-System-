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
            scheduled_at TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id)
        );
    """)

    # Ensure scheduled_at column exists for existing databases
    try:
        cursor.execute("ALTER TABLE notifications ADD COLUMN scheduled_at TIMESTAMP")
    except Exception:
        pass  # Column already exists

    # Seed questions if table is empty
    cursor.execute("SELECT COUNT(*) FROM questions")
    count = cursor.fetchone()[0]
    if count == 0:
        _seed_questions(cursor)

    conn.commit()
    conn.close()


def _seed_questions(cursor):
    """Seed the database with 1000 Python evaluation questions from question bank."""
    from app.question_bank import QUESTION_BANK

    data = [(q['question_text'], q['option_a'], q['option_b'], q['option_c'],
             q['option_d'], q['correct_answer'], q['difficulty'], q['topic'], 4)
            for q in QUESTION_BANK]
    cursor.executemany("""
        INSERT INTO questions (question_text, option_a, option_b, option_c, option_d,
                               correct_answer, difficulty, topic, marks)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)
