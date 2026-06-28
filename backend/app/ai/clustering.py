from typing import List, Dict, Any
import numpy as np
from sqlalchemy.orm import Session
import logging

from app.models.question import Question, QuestionEmbedding, QuestionCluster
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

def run_dbscan_clustering(embeddings: List[List[float]], eps: float = 0.18, min_samples: int = 1) -> List[int]:
    """Run DBSCAN clustering on embedding list using scikit-learn, with manual distance fallback."""
    try:
        from sklearn.cluster import DBSCAN
        matrix = np.array(embeddings)
        # Cosine distance = 1 - cosine similarity
        db = DBSCAN(eps=eps, min_samples=min_samples, metric="cosine").fit(matrix)
        return db.labels_.tolist()
        
    except ImportError:
        logger.warning("scikit-learn not available. Running manual distance clustering loop.")
        # Manual Fallback: basic agglomerative clustering based on similarity threshold
        n = len(embeddings)
        labels = [-1] * n
        cluster_id = 0
        
        # Simple distance grouping loop
        for i in range(n):
            if labels[i] != -1:
                continue
                
            labels[i] = cluster_id
            for j in range(i + 1, n):
                # Calculate cosine distance (1 - similarity)
                arr1 = np.array(embeddings[i])
                arr2 = np.array(embeddings[j])
                dot = np.dot(arr1, arr2)
                norm1 = np.linalg.norm(arr1)
                norm2 = np.linalg.norm(arr2)
                
                similarity = (dot / (norm1 * norm2)) if (norm1 > 0 and norm2 > 0) else 0.0
                distance = 1.0 - similarity
                
                if distance <= eps:
                    labels[j] = cluster_id
            cluster_id += 1
            
        return labels


def cluster_course_questions(db: Session, course_id: str) -> Dict[str, Any]:
    """Perform periodic database doubt clustering for a specific course module."""
    # 1. Fetch all active, unassigned questions in the course
    questions = db.query(Question).filter(
        Question.course_id == course_id,
        Question.status == "pending",
        Question.deleted_at.is_(None)
    ).all()
    
    if len(questions) < 2:
        return {"status": "skipped", "reason": "insufficient_questions"}

    # 2. Retrieve embeddings
    embeddings = []
    valid_questions = []
    for q in questions:
        emb_rec = db.query(QuestionEmbedding).filter(QuestionEmbedding.question_id == q.id).first()
        if emb_rec:
            embeddings.append(emb_rec.embedding)
            valid_questions.append(q)
            
    if len(embeddings) < 2:
        return {"status": "skipped", "reason": "insufficient_embeddings"}

    # 3. Compute clusters (DBSCAN Cosine threshold matches settings.AI_SIMILARITY_THRESHOLD)
    eps = 1.0 - settings.AI_SIMILARITY_THRESHOLD
    labels = run_dbscan_clustering(embeddings, eps=eps, min_samples=2)

    # 4. Group questions and save clusters in DB
    cluster_groups: Dict[int, List[Question]] = {}
    for idx, label in enumerate(labels):
        if label == -1:
            # Noise points are left as standalone doubts
            continue
        if label not in cluster_groups:
            cluster_groups[label] = []
        cluster_groups[label].append(valid_questions[idx])

    merged_count = 0
    # Process each identified cluster group
    for label, group in cluster_groups.items():
        # Check if any question in the group already belongs to a cluster
        existing_cluster_id = None
        for q in group:
            if q.cluster_id:
                existing_cluster_id = q.cluster_id
                break
                
        if existing_cluster_id:
            cluster = db.query(QuestionCluster).filter(QuestionCluster.id == existing_cluster_id).first()
        else:
            # Create new shared cluster
            cluster = QuestionCluster(
                course_id=course_id,
                status="pending",
                summary=f"AI Clustered Doubt: '{group[0].title}' and related issues."
            )
            db.add(cluster)
            db.flush()

        # Update all questions in the cluster group
        for q in group:
            if q.cluster_id != cluster.id:
                q.cluster_id = cluster.id
                q.status = "clustered"
                merged_count += 1
                
    db.commit()
    return {"status": "success", "clusters_formed": len(cluster_groups), "questions_merged": merged_count}
