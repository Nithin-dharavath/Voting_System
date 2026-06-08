import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from werkzeug.security import generate_password_hash
from app import app

client = TestClient(app)

@patch("app.get_db_cursor")
def test_register_student_success(mock_get_cursor):
    mock_cm = MagicMock()
    mock_cursor = MagicMock()
    mock_get_cursor.return_value = mock_cm
    mock_cm.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None

    import random
    import string
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    email = f"test_{random_str}@example.com"
    response = client.post("/auth/register", data={
        "full_name": "Test Student",
        "email": email,
        "password": "password123",
        "department": "Computer Science",
        "academic_year": "2023-24"
    })
    assert response.status_code == 200

def test_register_student_invalid_email():
    response = client.post("/auth/register", data={
        "full_name": "Test Student",
        "email": "invalid-email",
        "password": "password123",
        "department": "Computer Science",
        "academic_year": "2023-24"
    })
    assert response.status_code == 200
    assert "Invalid email format" in response.text

def test_register_student_short_password():
    import uuid
    email = f"test_{uuid.uuid4()}@example.com"
    response = client.post("/auth/register", data={
        "full_name": "Test Student",
        "email": email,
        "password": "short",
        "department": "Computer Science",
        "academic_year": "2023-24"
    })
    assert response.status_code == 200
    assert "Password must be at least 8 characters long" in response.text

@patch("app.get_db_cursor")
def test_student_login_success(mock_get_cursor):
    mock_cm = MagicMock()
    mock_cursor = MagicMock()
    mock_get_cursor.return_value = mock_cm
    mock_cm.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {
        "user_id": 1, "email": "student@example.com",
        "password_hash": generate_password_hash("password123"),
        "role": "STUDENT"
    }

    response = client.post("/auth/login", data={
        "email": "student@example.com",
        "password": "password123"
    }, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/student/dashboard?login=success"

@patch("app.get_db_cursor")
def test_student_login_invalid_password(mock_get_cursor):
    mock_cm = MagicMock()
    mock_cursor = MagicMock()
    mock_get_cursor.return_value = mock_cm
    mock_cm.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {
        "user_id": 1, "email": "student@example.com",
        "password_hash": generate_password_hash("password123"),
        "role": "STUDENT"
    }

    response = client.post("/auth/login", data={
        "email": "student@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 200
    assert "Invalid email or password" in response.text

@patch("app.get_db_cursor")
def test_admin_login_success(mock_get_cursor):
    mock_cm = MagicMock()
    mock_cursor = MagicMock()
    mock_get_cursor.return_value = mock_cm
    mock_cm.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {
        "user_id": 1, "email": "admin@example.com",
        "password_hash": generate_password_hash("adminpassword"),
        "role": "ADMIN"
    }

    response = client.post("/auth/admin-login", data={
        "email": "admin@example.com",
        "password": "adminpassword"
    }, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/dashboard?login=success"

def test_protected_route_redirect():
    # Attempt to access dashboard without token
    response = client.get("/student/dashboard", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"
