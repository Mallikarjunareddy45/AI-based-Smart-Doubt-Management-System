import pytest
from fastapi import status

def test_student_registration(client):
    """Test successful student sign up and base role assignment."""
    payload = {
        "email": "test.student@university.edu",
        "first_name": "Test",
        "last_name": "Student",
        "password": "strongpassword123",
        "role_names": ["student"]
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["first_name"] == payload["first_name"]
    assert data["is_active"] is True
    assert len(data["roles"]) == 1
    assert data["roles"][0]["name"] == "student"


def test_student_login(client):
    """Test standard OAuth2 client login credentials validation."""
    # 1. Register Student
    register_payload = {
        "email": "login.test@university.edu",
        "first_name": "Login",
        "last_name": "Test",
        "password": "securepassword",
        "role_names": ["student"]
    }
    client.post("/api/v1/auth/register", json=register_payload)

    # 2. Login Form Post
    login_data = {
        "username": "login.test@university.edu",
        "password": "securepassword"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == status.HTTP_200_OK
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"


def test_get_profile_me_unauthorized(client):
    """Test fetching private profile without header token results in 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
