import logging
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import type_coerce

from app.models.course import Course, Section, Lesson
from app.models.question import Question, QuestionCluster
from app.models.rag import LessonChunkEmbedding, AITutorConversation, AITutorMessage
from app.models.user import Student
from app.ai.embedding import generate_embedding
from app.ai.similarity import calculate_cosine_similarity

logger = logging.getLogger("uvicorn.error")

def chunk_text(text: str, max_words: int = 150, overlap_words: int = 30) -> List[str]:
    """Splits a document or note text into overlapping semantic chunks."""
    if not text or not text.strip():
        return []
        
    words = text.split()
    if len(words) <= max_words:
        return [text.strip()]
        
    chunks = []
    step = max_words - overlap_words
    for i in range(0, len(words), step):
        chunk_words = words[i : i + max_words]
        chunk_str = " ".join(chunk_words).strip()
        if chunk_str:
            chunks.append(chunk_str)
        if i + max_words >= len(words):
            break
            
    return chunks


def index_lesson_content(db: Session, lesson_id: UUID) -> int:
    """Extracts, chunks, embeds, and indexes a lesson's notes into vector storage."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        logger.error(f"Lesson {lesson_id} not found for indexing.")
        return 0

    section = db.query(Section).filter(Section.id == lesson.section_id).first()
    if not section:
        logger.error(f"Section for lesson {lesson_id} not found.")
        return 0

    # 1. Clear existing embeddings for this lesson
    db.query(LessonChunkEmbedding).filter(LessonChunkEmbedding.lesson_id == lesson_id).delete()
    db.flush()

    chunks_indexed = 0

    # 2. Index Notes Content
    if lesson.notes_content and lesson.notes_content.strip():
        notes_chunks = chunk_text(lesson.notes_content)
        for idx, text_chunk in enumerate(notes_chunks):
            # Create embedding vector
            full_context_str = f"Course Lesson: {lesson.title}\nSection: {section.title}\nContent:\n{text_chunk}"
            vector = generate_embedding(full_context_str)
            
            chunk_rec = LessonChunkEmbedding(
                course_id=section.course_id,
                section_id=section.id,
                lesson_id=lesson.id,
                content_chunk=text_chunk,
                chunk_type="notes",
                embedding=vector
            )
            db.add(chunk_rec)
            chunks_indexed += 1

    # 3. Index Video Metadata & Timestamped Markers if present
    if lesson.lesson_type == "video":
        video_context_str = f"Video Lesson Title: {lesson.title}. Section: {section.title}. Duration: {lesson.duration_seconds}s."
        vector = generate_embedding(video_context_str)
        chunk_rec = LessonChunkEmbedding(
            course_id=section.course_id,
            section_id=section.id,
            lesson_id=lesson.id,
            content_chunk=video_context_str,
            chunk_type="transcript",
            start_timestamp_seconds=0,
            end_timestamp_seconds=lesson.duration_seconds or 300,
            embedding=vector
        )
        db.add(chunk_rec)
        chunks_indexed += 1

    # 4. Index PDF Document Metadata if present
    if lesson.lesson_type == "pdf" and lesson.pdf_url:
        pdf_context_str = f"PDF Document: {lesson.title}. Section: {section.title}. URL: {lesson.pdf_url}"
        vector = generate_embedding(pdf_context_str)
        chunk_rec = LessonChunkEmbedding(
            course_id=section.course_id,
            section_id=section.id,
            lesson_id=lesson.id,
            content_chunk=pdf_context_str,
            chunk_type="pdf",
            embedding=vector
        )
        db.add(chunk_rec)
        chunks_indexed += 1

    db.commit()
    logger.info(f"Indexed {chunks_indexed} vector chunks for lesson '{lesson.title}' ({lesson.id})")
    return chunks_indexed


def search_knowledge_base(
    db: Session,
    course_id: UUID,
    query_text: str,
    active_lesson_id: Optional[UUID] = None,
    timestamp_seconds: Optional[int] = None,
    top_k: int = 4
) -> List[Dict[str, Any]]:
    """Performs RAG similarity search over indexed course material with optional video timestamp boosting."""
    query_vector = generate_embedding(query_text)
    
    # Query all embeddings for the course
    embeddings_in_course = (
        db.query(LessonChunkEmbedding, Lesson, Section)
        .join(Lesson, Lesson.id == LessonChunkEmbedding.lesson_id)
        .join(Section, Section.id == LessonChunkEmbedding.section_id)
        .filter(LessonChunkEmbedding.course_id == course_id)
        .all()
    )

    if not embeddings_in_course:
        return []

    scored_chunks = []
    for chunk, lesson, section in embeddings_in_course:
        base_sim = calculate_cosine_similarity(query_vector, chunk.embedding)
        
        # Apply timestamp & active lesson contextual boosting
        boost = 0.0
        if active_lesson_id and str(chunk.lesson_id) == str(active_lesson_id):
            boost += 0.15  # Boost active lesson content relevance
            
            if timestamp_seconds is not None and chunk.start_timestamp_seconds is not None:
                # Check timestamp proximity within 2 minutes
                if abs(timestamp_seconds - chunk.start_timestamp_seconds) <= 120:
                    boost += 0.20
                    
        final_score = min(1.0, base_sim + boost)
        
        snippet = chunk.content_chunk[:250] + "..." if len(chunk.content_chunk) > 250 else chunk.content_chunk
        scored_chunks.append({
            "chunk_id": str(chunk.id),
            "lesson_id": str(lesson.id),
            "lesson_title": lesson.title,
            "section_title": section.title,
            "chunk_type": chunk.chunk_type,
            "start_timestamp_seconds": chunk.start_timestamp_seconds,
            "snippet": snippet,
            "full_text": chunk.content_chunk,
            "similarity": round(final_score, 4)
        })

    # Sort descending by similarity
    scored_chunks.sort(key=lambda x: x["similarity"], reverse=True)
    return scored_chunks[:top_k]


def generate_tutor_response(
    db: Session,
    student_id: UUID,
    course_id: UUID,
    query_text: str,
    lesson_id: Optional[UUID] = None,
    timestamp_seconds: Optional[int] = None,
    conversation_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """RAG AI Tutor Answer Synthesizer with Citations & Low-Confidence Escalation Warning."""
    # 1. Fetch or create conversation
    if conversation_id:
        conversation = db.query(AITutorConversation).filter(
            AITutorConversation.id == conversation_id,
            AITutorConversation.student_id == student_id
        ).first()
    else:
        conversation = None

    if not conversation:
        title_summary = query_text[:35] + ("..." if len(query_text) > 35 else "")
        conversation = AITutorConversation(
            student_id=student_id,
            course_id=course_id,
            lesson_id=lesson_id,
            title=f"AI Tutor: {title_summary}"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # 2. Record User Prompt Message
    user_msg = AITutorMessage(
        conversation_id=conversation.id,
        sender="user",
        content=query_text,
        confidence_score=1.0
    )
    db.add(user_msg)

    # 3. Retrieve relevant chunks from RAG Knowledge Base
    retrieved_chunks = search_knowledge_base(
        db, course_id=course_id, query_text=query_text,
        active_lesson_id=lesson_id, timestamp_seconds=timestamp_seconds, top_k=4
    )

    # 4. Compute confidence score
    confidence_score = max([c["similarity"] for c in retrieved_chunks]) if retrieved_chunks else 0.0

    # 5. Synthesize Grounded AI Answer
    citations = []
    if retrieved_chunks and confidence_score >= 0.50:
        context_snippets = []
        for c in retrieved_chunks:
            time_ref = f" @ {c['start_timestamp_seconds']}s" if c['start_timestamp_seconds'] is not None else ""
            citations.append({
                "lesson_id": c["lesson_id"],
                "lesson_title": c["lesson_title"],
                "section_title": c["section_title"],
                "chunk_type": c["chunk_type"],
                "timestamp_seconds": c["start_timestamp_seconds"],
                "snippet": c["snippet"]
            })
            context_snippets.append(f"• In **{c['lesson_title']}** ({c['section_title']}{time_ref}): \"{c['snippet']}\"")
            
        timestamp_intro = f" (at video timestamp {timestamp_seconds}s)" if timestamp_seconds is not None else ""
        answer = (
            f"Here is what your course material explains regarding your question{timestamp_intro}:\n\n"
            + "\n\n".join(context_snippets)
            + "\n\nFeel free to ask further follow-up questions or jump directly to the cited lesson markers!"
        )
    else:
        answer = (
            "I searched your course knowledge base but could not find high-confidence matching content for your question.\n\n"
            "Would you like me to escalate this directly to your course instructor as a doubt query?"
        )

    # 6. Save AI Tutor Message
    ai_msg = AITutorMessage(
        conversation_id=conversation.id,
        sender="ai",
        content=answer,
        citations=citations,
        confidence_score=confidence_score,
        was_escalated=False
    )
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)

    return {
        "conversation_id": str(conversation.id),
        "message_id": str(ai_msg.id),
        "query": query_text,
        "answer": answer,
        "citations": citations,
        "confidence_score": confidence_score,
        "can_escalate": confidence_score < 0.55
    }


def escalate_to_instructor(db: Session, student_id: UUID, message_id: UUID) -> Dict[str, Any]:
    """Escalates a low-confidence AI message into an active student doubt question."""
    ai_msg = db.query(AITutorMessage).filter(AITutorMessage.id == message_id).first()
    if not ai_msg:
        raise ValueError("AI Tutor message not found")

    conversation = db.query(AITutorConversation).filter(AITutorConversation.id == ai_msg.conversation_id).first()
    if not conversation:
        raise ValueError("Conversation context not found")

    # Retrieve user prompt before this AI message
    user_prompt = db.query(AITutorMessage).filter(
        AITutorMessage.conversation_id == conversation.id,
        AITutorMessage.sender == "user",
        AITutorMessage.created_at <= ai_msg.created_at
    ).order_by(AITutorMessage.created_at.desc()).first()

    title_text = user_prompt.content[:80] if user_prompt else "AI Tutor Escalated Doubt"
    content_text = f"**Escalated from AI Tutor**\n\nStudent Query: {user_prompt.content if user_prompt else 'N/A'}\n\nAI Confidence Score: {ai_msg.confidence_score:.2f}"

    # 1. Create Student Question
    new_question = Question(
        student_id=student_id,
        course_id=conversation.course_id,
        title=f"[AI Escalated] {title_text}",
        content=content_text,
        status="pending",
        urgency_score=1.0,
        priority_score=1.0
    )
    db.add(new_question)
    ai_msg.was_escalated = True
    db.commit()
    db.refresh(new_question)

    return {
        "question_id": str(new_question.id),
        "title": new_question.title,
        "status": new_question.status
    }
