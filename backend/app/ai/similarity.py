from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import type_coerce
import numpy as np
import logging

from app.models.question import Question, QuestionEmbedding, QuestionCluster
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

def calculate_cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Manually calculate cosine similarity between two float arrays."""
    arr1 = np.array(v1)
    arr2 = np.array(v2)
    dot_product = np.dot(arr1, arr2)
    norm1 = np.linalg.norm(arr1)
    norm2 = np.linalg.norm(arr2)
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return float(dot_product / (norm1 * norm2))


def find_similar_questions_db(
    db: Session, 
    embedding: List[float], 
    course_id: str, 
    threshold: float = None
) -> List[Tuple[Question, float]]:
    """Query nearest neighbor questions using pgvector distance operators, with NumPy fallback."""
    if threshold is None:
        threshold = settings.AI_SIMILARITY_THRESHOLD
        
    distance_threshold = 1.0 - threshold
    
    try:
        # Cosine distance operator <=> in Postgres
        # We can construct the custom operator mapping using SQLAlchemy .op()
        # This prevents AttributeError if pgvector package isn't imported
        dist_op = QuestionEmbedding.embedding.op('<=>')(embedding)
        
        results = (
            db.query(QuestionEmbedding, Question, dist_op.label("distance"))
            .join(Question, Question.id == QuestionEmbedding.question_id)
            .filter(
                Question.course_id == course_id,
                Question.deleted_at.is_(None),
                dist_op <= distance_threshold
            )
            .order_by("distance")
            .limit(5)
            .all()
        )
        
        # results contains: (QuestionEmbedding, Question, distance)
        return [(q, 1.0 - float(dist)) for _, q, dist in results]
        
    except Exception as e:
        logger.warning(f"pgvector query failed: {e}. Falling back to manual NumPy scans.")
        
        # NumPy Fallback: Load active questions in the course and scan manually
        all_embeddings = (
            db.query(QuestionEmbedding, Question)
            .join(Question, Question.id == QuestionEmbedding.question_id)
            .filter(
                Question.course_id == course_id,
                Question.deleted_at.is_(None)
            )
            .all()
        )
        
        matches = []
        for emb_record, question in all_embeddings:
            # emb_record.embedding can be a list or array
            emb_vector = emb_record.embedding
            if isinstance(emb_vector, bytes):
                # Handle potential binary storage formats
                continue
            sim = calculate_cosine_similarity(embedding, emb_vector)
            if sim >= threshold:
                matches.append((question, sim))
                
        # Sort by similarity descending
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:5]
