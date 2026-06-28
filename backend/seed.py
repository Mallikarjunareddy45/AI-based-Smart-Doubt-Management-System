import sys
import os

# Inject backend directory into python path to allow imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.course import Course

def seed_courses():
    db = SessionLocal()
    try:
        # Guarantee subjects column exists in postgres
        from sqlalchemy import text
        try:
            db.execute(text("ALTER TABLE tutor ADD COLUMN IF NOT EXISTS subjects VARCHAR(500) DEFAULT '';"))
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Altering tutor table skipped/already done: {e}")
            
        sample_courses = [
            {"code": "CS-101", "title": "Python Programming", "description": "Core concepts of programming, syntax, control flows, and object-oriented programming in Python."},
            {"code": "CS-102", "title": "Data Structures", "description": "Structures for organizing data, including lists, stacks, queues, hash tables, trees, and graphs."},
            {"code": "CS-103", "title": "DBMS", "description": "Relational database models, SQL language, normalization (3NF), transaction management, and indexing concepts."},
            {"code": "CS-201", "title": "Machine Learning", "description": "Introduction to supervised and unsupervised algorithms, regression, support vector machines, and clustering."},
            {"code": "CS-202", "title": "Deep Learning", "description": "Neural network architectures, backpropagation, convolutional layers (CNNs), and recurrent layers (RNNs)."},
            {"code": "CS-203", "title": "Artificial Intelligence", "description": "Search trees, heuristics, adversarial games, constraint satisfaction, logic, and probabilistic reasoning."},
            {"code": "CS-301", "title": "Operating Systems", "description": "Processes, threads, scheduling algorithms, memory paging, deadlocks, and virtual memory filesystems."},
            {"code": "CS-302", "title": "Computer Networks", "description": "OSI network reference model layers, TCP/IP configurations, routers, firewalls, and DNS pub-subs."},
            {"code": "CS-303", "title": "React", "description": "Modern frontend single page applications, React Hooks, virtual DOM, states, and responsive styling systems."},
            {"code": "CS-304", "title": "FastAPI", "description": "Asynchronous REST API servers in Python, dependencies injection, pydantic validations, and database integrations."},
            {"code": "CS-104", "title": "Java", "description": "Object-oriented programming using Java, JVM architecture, multithreading, and collections framework."},
            {"code": "CS-401", "title": "Cloud Computing", "description": "Cloud architectures, virtualizations, serverless functions, AWS/GCP services, and resource scaling."},
            {"code": "CS-204", "title": "NLP", "description": "Natural language processing, word tokenization, TF-IDF, POS tagging, and transformer-based language models."},
            {"code": "CS-105", "title": "SQL", "description": "Structured Query Language, complex joins, subqueries, analytical window functions, and database triggers."},
            {"code": "CS-402", "title": "Docker", "description": "Containerizations, images compilation, volumes mounting, network orchestration, and multi-service compose clusters."}
        ]

        seeded_count = 0
        for data in sample_courses:
            existing = db.query(Course).filter(Course.code == data["code"]).first()
            if not existing:
                course = Course(
                    code=data["code"],
                    title=data["title"],
                    description=data["description"]
                )
                db.add(course)
                seeded_count += 1
            else:
                # If deleted, reactivate it
                if existing.deleted_at is not None:
                    existing.deleted_at = None
                    existing.title = data["title"]
                    existing.description = data["description"]
                    db.add(existing)
                    seeded_count += 1

        db.commit()
        print(f"Database seeding completed! Added/updated {seeded_count} courses.")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_courses()
