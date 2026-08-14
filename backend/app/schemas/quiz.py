from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from uuid import UUID

class QuizQuestionResponse(BaseModel):
    id: str
    question_text: str
    question_type: str
    options: Optional[List[str]] = None
    concept_tag: str
    points: int
    order: int

class QuizResponse(BaseModel):
    id: str
    course_id: str
    section_id: Optional[str] = None
    lesson_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    passing_score_percentage: float
    time_limit_minutes: Optional[int] = None
    is_ai_generated: bool
    questions: List[QuizQuestionResponse] = []

class QuizSubmissionRequest(BaseModel):
    answers: Dict[str, str] # question_id -> student_answer
    time_spent_seconds: Optional[int] = 0

class QuizAnswerFeedback(BaseModel):
    question_id: str
    question_text: str
    student_answer: Optional[str] = None
    correct_answer: str
    is_correct: bool
    explanation: Optional[str] = None
    feedback: Optional[str] = None
    concept_tag: str

class QuizSubmissionResponse(BaseModel):
    attempt_id: str
    quiz_id: str
    score_percentage: float
    points_earned: int
    total_points: int
    passed: bool
    time_spent_seconds: int
    answer_feedbacks: List[QuizAnswerFeedback] = []

class ConceptPerformanceItem(BaseModel):
    concept_tag: str
    total_questions: int
    correct_answers: int
    accuracy_percentage: float

class RecommendedLessonItem(BaseModel):
    lesson_id: str
    title: str
    lesson_type: str

class WeaknessAnalysisResponse(BaseModel):
    student_id: str
    course_id: str
    total_attempts: int
    overall_accuracy_percentage: float
    concept_performance: List[ConceptPerformanceItem] = []
    weak_concepts: List[str] = []
    recommended_lessons: List[RecommendedLessonItem] = []
