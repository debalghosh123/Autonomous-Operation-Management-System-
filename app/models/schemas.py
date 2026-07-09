"""
Career Lab Consulting - Pydantic Schemas
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class CandidateCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None


class CandidateResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    registered_at: Optional[str] = None
    is_active: int = 1


class ExamCreate(BaseModel):
    candidate_id: int


class ExamResponse(BaseModel):
    id: int
    candidate_id: int
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    score: int = 0
    total_marks: int = 100
    percentage: float = 0.0
    passed: int = 0


class AnswerSubmit(BaseModel):
    exam_id: int
    question_id: int
    selected_answer: str


class ExamResult(BaseModel):
    exam_id: int
    candidate_name: str
    score: int
    total_marks: int
    percentage: float
    passed: bool
    ai_feedback: Optional[str] = None
    total_questions: int = 50
    correct_answers: int = 0


class AdminLogin(BaseModel):
    username: str
    password: str


class QuestionSchema(BaseModel):
    id: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    difficulty: str
    topic: str
    marks: int = 4


class NotificationRequest(BaseModel):
    candidate_id: int
    type: str  # email or whatsapp
    message: str


class VoiceCommand(BaseModel):
    command: str
    exam_id: Optional[int] = None
