from typing import List
import logging
from datetime import datetime

from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.user import User, Tutor
from app.models.question import Question, QuestionCluster, QuestionEmbedding, TutorAssignment
from app.models.notification import Notification
from app.ai.embedding import generate_embedding
from app.ai.similarity import find_similar_questions_db
from app.core.config import settings
from app.core.ws_manager import manager

logger = logging.getLogger("celery.task")

@celery_app.task(name="app.workers.tasks.analyze_question_task")
def analyze_question_task(question_id: str) -> str:
    """Core AI processing worker. Handles embedding, clustering, priority, and routing."""
    db = SessionLocal()
    try:
        # 1. Retrieve the question
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            logger.error(f"Question {question_id} not found in database.")
            return "failed: question_not_found"

        # 2. Generate text embedding (concatenate title and content)
        text_to_encode = f"{question.title}\n{question.content}"
        vector = generate_embedding(text_to_encode)
        
        # Save or update question embedding record
        embedding_record = db.query(QuestionEmbedding).filter(QuestionEmbedding.question_id == question.id).first()
        if not embedding_record:
            embedding_record = QuestionEmbedding(question_id=question.id, embedding=vector)
            db.add(embedding_record)
        else:
            embedding_record.embedding = vector
        db.flush()

        # 3. Urgency and priority scoring (text keyword blockers and upvotes)
        content_lower = text_to_encode.lower()
        urgency = 0.0
        for kw in settings.AI_URGENCY_KEYWORDS:
            if kw in content_lower:
                urgency += 1.0  # Increment for each blocker keyword matched
                
        question.urgency_score = urgency
        # Base priority = urgency + wait time component + upvotes
        wait_hours = (datetime.utcnow() - question.created_at).total_seconds() / 3600.0
        question.priority_score = urgency + (wait_hours * 0.2) + (question.upvotes_count * 0.5)
        db.flush()

        # 4. Duplicate matching & Clustering
        similar_questions = find_similar_questions_db(
            db, vector, str(question.course_id), settings.AI_SIMILARITY_THRESHOLD
        )
        
        cluster = None
        
        # Check if we have a semantically similar match in this course
        if similar_questions:
            # Match found! Join the cluster of the most similar question
            matched_question, similarity = similar_questions[0]
            logger.info(f"Doubt {question.id} matches doubt {matched_question.id} with similarity {similarity:.2f}")
            
            if matched_question.cluster_id:
                # Join existing cluster
                cluster = db.query(QuestionCluster).filter(QuestionCluster.id == matched_question.cluster_id).first()
                if cluster:
                    question.cluster_id = cluster.id
                    question.status = "clustered"
            else:
                # Matched question has no cluster yet. Create a new cluster for both.
                cluster = QuestionCluster(
                    course_id=question.course_id,
                    status="pending",
                    summary=f"Clustered doubt: '{matched_question.title}' and similar concerns."
                )
                db.add(cluster)
                db.flush()
                
                matched_question.cluster_id = cluster.id
                matched_question.status = "clustered"
                question.cluster_id = cluster.id
                question.status = "clustered"
        
        if not cluster:
            # No match found. Create a new standalone cluster for this question.
            cluster = QuestionCluster(
                course_id=question.course_id,
                status="pending",
                summary=f"Doubt cluster: {question.title}"
            )
            db.add(cluster)
            db.flush()
            
            question.cluster_id = cluster.id
            question.status = "clustered"
            
        db.flush()

        # 5. Update Cluster Priority Score (Max of clustered questions priority)
        clustered_priorities = [q.priority_score for q in cluster.questions]
        cluster.priority_score = max(clustered_priorities) if clustered_priorities else question.priority_score
        db.flush()

        # 6. Load-Balanced Tutor Routing Matching Subject
        if cluster.assigned_tutor_id is None:
            from app.models.course import Course
            course = db.query(Course).filter(Course.id == question.course_id).first()
            course_title = course.title.lower() if course else ""
            course_code = course.code.lower() if course else ""

            # Fetch active, available tutors
            available_tutors = db.query(Tutor).filter(Tutor.is_available == True).all()
            if available_tutors:
                # Load balance: Pick the tutor with the lowest active workload matching subject
                tutor_workloads = []
                for tutor in available_tutors:
                    tutor_subjects = [s.strip().lower() for s in (tutor.subjects or "").split(",") if s.strip()]
                    matches_subject = (
                        not tutor_subjects or
                        any(sub in course_title or sub in course_code for sub in tutor_subjects) or
                        any(course_title in sub or course_code in sub for sub in tutor_subjects)
                    )
                    
                    if not matches_subject:
                        continue

                    active_load = db.query(QuestionCluster).filter(
                        QuestionCluster.assigned_tutor_id == tutor.user_id,
                        QuestionCluster.status != "resolved"
                    ).count()
                    
                    if active_load < tutor.max_workload:
                        tutor_workloads.append((tutor, active_load))
                        
                if tutor_workloads:
                    # Sort by workload ascending, pick the lowest
                    tutor_workloads.sort(key=lambda x: x[1])
                    selected_tutor = tutor_workloads[0][0]
                    
                    # Assign tutor
                    cluster.assigned_tutor_id = selected_tutor.user_id
                    cluster.status = "assigned"
                    
                    # Save assignment audit
                    assignment = TutorAssignment(
                        cluster_id=cluster.id,
                        tutor_id=selected_tutor.user_id,
                        status="active",
                        assigned_by=None # Assigned automatically by AI engine
                    )
                    db.add(assignment)
                    logger.info(f"AI auto-routed cluster {cluster.id} to tutor {selected_tutor.user_id} (active load: {tutor_workloads[0][1]})")
                    
                    # Create Notification for Tutor
                    tutor_notif = Notification(
                        recipient_id=selected_tutor.user_id,
                        title="New Doubt Cluster Assigned",
                        content=f"You have been assigned cluster '{cluster.summary[:50]}...' with priority {cluster.priority_score:.1f}.",
                        type="cluster_assigned",
                        is_read=False
                    )
                    db.add(tutor_notif)
                    
        # 7. Create Notification for Student
        student_notif = Notification(
            recipient_id=question.student_id,
            title="Doubt Processed",
            content=f"Your question has been clustered. Status: {cluster.status}.",
            type="doubt_processed",
            is_read=False
        )
        db.add(student_notif)
        db.commit()

        # 8. Dispatch real-time WebSocket push updates
        try:
            import asyncio
            # Build payload
            payload = {
                "event": "question_analyzed",
                "question_id": str(question.id),
                "cluster_id": str(cluster.id),
                "status": cluster.status,
                "assigned_tutor_id": str(cluster.assigned_tutor_id) if cluster.assigned_tutor_id else None
            }
            # Since celery task is synchronous running in background worker process, we can run async loop block
            asyncio.run(manager.broadcast_to_cluster(payload, str(cluster.id)))
            # Also notify tutors and admins to reload queues
            asyncio.run(manager.broadcast_to_tutors({"event": "queue_updated"}))
            asyncio.run(manager.broadcast_to_admins({"event": "queue_updated"}))
        except Exception as ws_err:
            logger.warning(f"Celery WS broadcast skipped (separate worker space): {ws_err}")

        return "success"
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to process AI analysis: {e}")
        return f"failed: {e}"
    finally:
        db.close()
