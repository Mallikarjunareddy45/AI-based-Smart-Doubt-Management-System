import logging
import uuid
from uuid import UUID
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.course import Course, Section, Lesson
from app.models.quiz import Quiz, QuizQuestion, QuizAttempt, QuizAnswer
from app.models.user import Student

logger = logging.getLogger("uvicorn.error")

def generate_quiz_questions_from_text(lesson_title: str, text_content: str, num_questions: int = 5) -> List[Dict[str, Any]]:
    """Synthesizes structured quiz questions with options, correct answer, explanation, and concept tags."""
    sample_questions = []
    
    # Extract key lines or paragraphs for context
    lines = [l.strip() for l in text_content.split("\n") if len(l.strip()) > 15] if text_content else []

    # Question 1: Core Concept Definition
    q1_concept = f"{lesson_title} Fundamentals"
    q1_text = f"What is the primary objective of '{lesson_title}'?"
    q1_opts = [
        f"To understand and apply key principles of {lesson_title}",
        f"To ignore fundamental definitions and skip practical syntax",
        f"To replace database indexes with unindexed flat text files",
        f"To disable real-time state synchronization across all modules"
    ]
    sample_questions.append({
        "question_text": q1_text,
        "question_type": "multiple_choice",
        "options": q1_opts,
        "correct_answer": q1_opts[0],
        "explanation": f"The primary goal of '{lesson_title}' is to build a solid comprehension of core domain concepts and operational syntax.",
        "concept_tag": q1_concept,
        "points": 1,
        "order": 1
    })

    # Question 2: Specific Detail / Content Statement
    if lines:
        sample_fact = lines[0][:100]
        q2_concept = f"{lesson_title} Implementation"
        q2_text = f"According to lesson notes: '{sample_fact}...', which statement is ACCURATE?"
        q2_opts = [
            f"Statement is valid and represents standard best practices in {lesson_title}",
            f"Statement is completely invalid and causes memory overflow errors",
            f"Statement only applies when running legacy single-threaded architectures",
            f"Statement requires disabling system security and authentication"
        ]
        sample_questions.append({
            "question_text": q2_text,
            "question_type": "multiple_choice",
            "options": q2_opts,
            "correct_answer": q2_opts[0],
            "explanation": f"The lesson notes emphasize that '{sample_fact}...' is correct behavior.",
            "concept_tag": q2_concept,
            "points": 1,
            "order": 2
        })

    # Question 3: True / False Concept Check
    q3_concept = f"{lesson_title} Best Practices"
    q3_text = f"True or False: Mastering {lesson_title} improves overall system reliability and accuracy."
    q3_opts = ["True", "False"]
    sample_questions.append({
        "question_text": q3_text,
        "question_type": "true_false",
        "options": q3_opts,
        "correct_answer": "True",
        "explanation": f"True. Proper implementation of {lesson_title} principles leads to higher reliability.",
        "concept_tag": q3_concept,
        "points": 1,
        "order": 3
    })

    # Additional Questions if requested
    if num_questions >= 4:
        q4_concept = f"{lesson_title} Edge Cases"
        q4_text = f"How should edge case exceptions be handled in {lesson_title}?"
        q4_opts = [
            "Gracefully log error context and enforce safe fallbacks",
            "Ignore exceptions silently and return 0-byte null data",
            "Crash the entire backend application server immediately",
            "Bypass role checks and grant full superuser privileges"
        ]
        sample_questions.append({
            "question_text": q4_text,
            "question_type": "multiple_choice",
            "options": q4_opts,
            "correct_answer": q4_opts[0],
            "explanation": "Standard production resilience guidelines dictate graceful exception handling and safe fallback returns.",
            "concept_tag": q4_concept,
            "points": 1,
            "order": 4
        })

    if num_questions >= 5:
        q5_concept = f"{lesson_title} Optimization"
        q5_text = f"What is the recommended approach for optimizing performance in {lesson_title}?"
        q5_opts = [
            "Utilize vector indexes and lazy model initialization",
            "Execute blocking synchronous loops on the main thread",
            "Re-download large model weights on every API request",
            "Disable memory caching entirely"
        ]
        sample_questions.append({
            "question_text": q5_text,
            "question_type": "multiple_choice",
            "options": q5_opts,
            "correct_answer": q5_opts[0],
            "explanation": "Performance optimization relies on indexing, lazy loading, and efficient async caching.",
            "concept_tag": q5_concept,
            "points": 1,
            "order": 5
        })

    return sample_questions[:num_questions]


def generate_quiz_for_lesson(
    db: Session,
    lesson_id: UUID,
    num_questions: int = 5,
    difficulty: str = "medium"
) -> Quiz:
    """Generates an AI Quiz for a specific lesson and persists Quiz and QuizQuestion records."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise ValueError(f"Lesson {lesson_id} not found")

    section = db.query(Section).filter(Section.id == lesson.section_id).first()
    if not section:
        raise ValueError(f"Section for lesson {lesson_id} not found")

    # 1. Create Quiz Header
    quiz = Quiz(
        course_id=section.course_id,
        section_id=section.id,
        lesson_id=lesson.id,
        title=f"Quiz: {lesson.title}",
        description=f"Automated AI Knowledge Assessment for '{lesson.title}'. Difficulty: {difficulty.capitalize()}.",
        passing_score_percentage=70.0,
        time_limit_minutes=15,
        is_ai_generated=True
    )
    db.add(quiz)
    db.flush()

    # 2. Synthesize Questions
    raw_questions = generate_quiz_questions_from_text(lesson.title, lesson.notes_content or "", num_questions)

    for q_data in raw_questions:
        qq = QuizQuestion(
            quiz_id=quiz.id,
            question_text=q_data["question_text"],
            question_type=q_data["question_type"],
            options=q_data["options"],
            correct_answer=q_data["correct_answer"],
            explanation=q_data["explanation"],
            concept_tag=q_data["concept_tag"],
            points=q_data["points"],
            order=q_data["order"]
        )
        db.add(qq)

    db.commit()
    db.refresh(quiz)
    logger.info(f"Generated AI Quiz '{quiz.title}' ({quiz.id}) with {len(raw_questions)} questions.")
    return quiz


def evaluate_quiz_submission(
    db: Session,
    student_id: UUID,
    quiz_id: UUID,
    submitted_answers: Dict[str, str], # question_id (str) -> student_answer (str)
    time_spent_seconds: int = 0
) -> QuizAttempt:
    """Evaluates student quiz attempt, computes scores, and generates detailed feedback."""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise ValueError(f"Quiz {quiz_id} not found")

    questions = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz.id).order_by(QuizQuestion.order).all()
    if not questions:
        raise ValueError("Quiz has no questions")

    total_points = sum([q.points for q in questions])
    points_earned = 0

    attempt = QuizAttempt(
        quiz_id=quiz.id,
        student_id=student_id,
        total_points=total_points,
        time_spent_seconds=time_spent_seconds
    )
    db.add(attempt)
    db.flush()

    for q in questions:
        q_id_str = str(q.id)
        user_ans = submitted_answers.get(q_id_str, "").strip()
        
        # Check correctness
        is_corr = (user_ans.lower() == q.correct_answer.lower())
        if is_corr:
            points_earned += q.points
            feedback_str = f"Correct! {q.explanation or ''}"
        else:
            feedback_str = f"Incorrect. Correct Answer: '{q.correct_answer}'. Explanation: {q.explanation or 'Review lesson material.'}"

        ans_rec = QuizAnswer(
            attempt_id=attempt.id,
            question_id=q.id,
            student_answer=user_ans,
            is_correct=is_corr,
            feedback=feedback_str
        )
        db.add(ans_rec)

    score_pct = round((points_earned / total_points) * 100.0, 2) if total_points > 0 else 0.0
    passed_flag = score_pct >= quiz.passing_score_percentage

    attempt.points_earned = points_earned
    attempt.score_percentage = score_pct
    attempt.passed = passed_flag

    db.commit()
    db.refresh(attempt)
    logger.info(f"Student {student_id} submitted quiz {quiz.id}: Score {score_pct}% (Passed: {passed_flag})")
    return attempt


def analyze_student_weaknesses(db: Session, student_id: UUID, course_id: UUID) -> Dict[str, Any]:
    """Analyzes student quiz history in a course to identify weak concept tags and recommend lessons."""
    attempts = (
        db.query(QuizAttempt)
        .join(Quiz, Quiz.id == QuizAttempt.quiz_id)
        .filter(QuizAttempt.student_id == student_id, Quiz.course_id == course_id)
        .all()
    )

    if not attempts:
        return {
            "student_id": str(student_id),
            "course_id": str(course_id),
            "total_attempts": 0,
            "overall_accuracy_percentage": 0.0,
            "concept_performance": [],
            "weak_concepts": [],
            "recommended_lessons": []
        }

    attempt_ids = [a.id for a in attempts]
    answers = (
        db.query(QuizAnswer, QuizQuestion)
        .join(QuizQuestion, QuizQuestion.id == QuizAnswer.question_id)
        .filter(QuizAnswer.attempt_id.in_(attempt_ids))
        .all()
    )

    concept_stats = {}
    for ans, q in answers:
        tag = q.concept_tag or "General Concept"
        if tag not in concept_stats:
            concept_stats[tag] = {"total": 0, "correct": 0, "lesson_id": q.quiz.lesson_id if q.quiz else None}
        concept_stats[tag]["total"] += 1
        if ans.is_correct:
            concept_stats[tag]["correct"] += 1

    concept_performance = []
    weak_concepts = []
    recommended_lesson_ids = set()

    for tag, stats in concept_stats.items():
        acc = round((stats["correct"] / stats["total"]) * 100.0, 1) if stats["total"] > 0 else 0.0
        item = {
            "concept_tag": tag,
            "total_questions": stats["total"],
            "correct_answers": stats["correct"],
            "accuracy_percentage": acc
        }
        concept_performance.append(item)
        if acc < 70.0:
            weak_concepts.append(tag)
            if stats["lesson_id"]:
                recommended_lesson_ids.add(stats["lesson_id"])

    # Fetch lesson metadata for recommendations
    recommended_lessons = []
    if recommended_lesson_ids:
        rec_lessons = db.query(Lesson).filter(Lesson.id.in_(list(recommended_lesson_ids))).all()
        for les in rec_lessons:
            recommended_lessons.append({
                "lesson_id": str(les.id),
                "title": les.title,
                "lesson_type": les.lesson_type
            })

    total_qs = len(answers)
    total_corr = sum([1 for ans, q in answers if ans.is_correct])
    overall_acc = round((total_corr / total_qs) * 100.0, 1) if total_qs > 0 else 0.0

    return {
        "student_id": str(student_id),
        "course_id": str(course_id),
        "total_attempts": len(attempts),
        "overall_accuracy_percentage": overall_acc,
        "concept_performance": concept_performance,
        "weak_concepts": weak_concepts,
        "recommended_lessons": recommended_lessons
    }


def generate_adaptive_practice(db: Session, student_id: UUID, course_id: UUID, num_questions: int = 4) -> Quiz:
    """Generates an Adaptive AI Practice session targeting identified student concept weaknesses."""
    weakness_data = analyze_student_weaknesses(db, student_id, course_id)
    weak_tags = weakness_data.get("weak_concepts", [])

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise ValueError(f"Course {course_id} not found")

    target_tag = weak_tags[0] if weak_tags else "General Course Practice"

    quiz = Quiz(
        course_id=course.id,
        title=f"Adaptive Practice: {target_tag}",
        description=f"AI-Generated Adaptive Practice Session targeting weak areas ({target_tag}).",
        passing_score_percentage=70.0,
        time_limit_minutes=10,
        is_ai_generated=True
    )
    db.add(quiz)
    db.flush()

    raw_questions = generate_quiz_questions_from_text(target_tag, f"Adaptive practice for concept: {target_tag}", num_questions)

    for q_data in raw_questions:
        qq = QuizQuestion(
            quiz_id=quiz.id,
            question_text=f"[Adaptive Practice] {q_data['question_text']}",
            question_type=q_data["question_type"],
            options=q_data["options"],
            correct_answer=q_data["correct_answer"],
            explanation=q_data["explanation"],
            concept_tag=target_tag,
            points=q_data["points"],
            order=q_data["order"]
        )
        db.add(qq)

    db.commit()
    db.refresh(quiz)
    logger.info(f"Generated Adaptive Practice Quiz '{quiz.title}' ({quiz.id}) for student {student_id}")
    return quiz
