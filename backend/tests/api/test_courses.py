import pytest
from fastapi import status
from app.core.security import create_access_token
from app.models.user import Role

def test_course_lifecycle_and_doubt_routing(client, db):
    """E2E Verification of Course Creation, Enrollment, and Doubt Submission."""
    # 1. Setup default roles in database
    student_role = Role(name="student", description="Student privileges")
    admin_role = Role(name="admin", description="Admin overrides")
    db.add(student_role)
    db.add(admin_role)
    db.commit()

    # 2. Register Student & Admin users
    student_payload = {
        "email": "student@university.edu",
        "first_name": "Albus",
        "last_name": "Potter",
        "password": "hashedpassword123",
        "role_names": ["student"]
    }
    
    # Register student publicly
    client.post("/api/v1/auth/register", json=student_payload)
    
    # Register admin directly in database for security compliance
    from app.models.user import User
    from app.core.security import get_password_hash
    admin_user = User(
        email="admin@university.edu",
        hashed_password=get_password_hash("adminpassword123"),
        first_name="Minerva",
        last_name="McGonagall",
        is_active=True
    )
    admin_user.roles.append(admin_role)
    db.add(admin_user)
    db.commit()

    # 3. Authenticate both users to obtain JWT tokens
    # Student login
    student_login = client.post("/api/v1/auth/login", data={"username": "student@university.edu", "password": "hashedpassword123"})
    student_token = student_login.json()["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # Admin login
    admin_login = client.post("/api/v1/auth/login", data={"username": "admin@university.edu", "password": "adminpassword123"})
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 4. Admin creates a new course
    course_payload = {
        "code": "CS-202",
        "title": "Systems Programming",
        "description": "Introduction to concurrent processes, signals, and shared memory in Unix."
    }
    course_res = client.post("/api/v1/admin/courses", json=course_payload, headers=admin_headers)
    assert course_res.status_code == status.HTTP_201_CREATED
    course_id = course_res.json()["id"]

    # 5. Student browses available courses
    catalog_res = client.get("/api/v1/students/courses/available", headers=student_headers)
    assert catalog_res.status_code == status.HTTP_200_OK
    catalog = catalog_res.json()
    assert len(catalog) == 1
    assert catalog[0]["code"] == "CS-202"

    # 6. Student enrolls in CS-202
    enroll_payload = {"course_id": course_id}
    enroll_res = client.post("/api/v1/students/courses/enroll", json=enroll_payload, headers=student_headers)
    assert enroll_res.status_code == status.HTTP_201_CREATED
    assert enroll_res.json()["status"] == "active"

    # 7. Student checks enrolled list (My Active Courses)
    enrolled_res = client.get("/api/v1/students/courses", headers=student_headers)
    assert enrolled_res.status_code == status.HTTP_200_OK
    assert len(enrolled_res.json()) == 1
    assert enrolled_res.json()[0]["course"]["code"] == "CS-202"

    # 8. Student submits a doubt in CS-202
    doubt_payload = {
        "title": "IPC Pipe Blocking Behavior",
        "content": "Why does a read block on a pipe if the write descriptor is still open in another process?",
        "course_id": course_id
    }
    doubt_res = client.post("/api/v1/questions/", json=doubt_payload, headers=student_headers)
    assert doubt_res.status_code == status.HTTP_201_CREATED
    doubt_data = doubt_res.json()
    assert doubt_data["title"] == doubt_payload["title"]

    # 9. Student retrieves list of asked doubts (My Doubts)
    my_doubts_res = client.get("/api/v1/students/questions", headers=student_headers)
    assert my_doubts_res.status_code == status.HTTP_200_OK
    my_doubts = my_doubts_res.json()
    assert len(my_doubts) == 1
    assert my_doubts[0]["title"] == "IPC Pipe Blocking Behavior"
