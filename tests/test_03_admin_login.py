from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from werkzeug.security import generate_password_hash

from app import COOKIE_NAME, app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def mock_cursor():
    with patch("app.get_db_cursor") as mock_get_cursor:
        mock_cm = MagicMock()
        mock_cursor_obj = MagicMock()
        mock_get_cursor.return_value = mock_cm
        mock_cm.__enter__.return_value = mock_cursor_obj
        yield mock_cursor_obj

@pytest.fixture
def student_user():
    return {
        "user_id": 1,
        "email": "student@example.com",
        "password_hash": generate_password_hash("studentpass123"),
        "role": "STUDENT"
    }

@pytest.fixture
def admin_user():
    return {
        "user_id": 2,
        "email": "admin@example.com",
        "password_hash": generate_password_hash("adminpass123"),
        "role": "ADMIN"
    }

def test_admin_login_page(client):
    """Test that GET /admin/login renders the admin login form."""
    response = client.get("/admin/login")
    assert response.status_code == 200
    assert "admin-login.html" in response.text or "Admin Login" in response.text # Depending on template content

def test_admin_login_page_form_action(client):
    """Test that the admin login form posts to /auth/admin-login."""
    response = client.get("/admin/login")
    assert response.status_code == 200
    assert 'action="/auth/admin-login"' in response.text

def test_admin_login_success(client, mock_cursor, admin_user):
    """Test successful admin login via /auth/admin-login."""
    mock_cursor.fetchone.return_value = admin_user

    payload = {
        "email": admin_user["email"],
        "password": "adminpass123"
    }

    response = client.post("/auth/admin-login", data=payload, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/dashboard?login=success"
    assert client.cookies.get(COOKIE_NAME) is not None

def test_admin_login_invalid_credentials(client, mock_cursor):
    """Test admin login fails with invalid credentials."""
    mock_cursor.fetchone.return_value = None

    payload = {"email": "nonexistent@example.com", "password": "password123"}
    response = client.post("/auth/admin-login", data=payload)

    assert response.status_code == 200
    assert "Invalid email or password" in response.text

def test_admin_login_wrong_password(client, mock_cursor, admin_user):
    """Test admin login fails with wrong password."""
    mock_cursor.fetchone.return_value = admin_user

    payload = {"email": admin_user["email"], "password": "wrongpassword"}
    response = client.post("/auth/admin-login", data=payload)

    assert response.status_code == 200
    assert "Invalid email or password" in response.text

def test_admin_login_student_rejected(client, mock_cursor, student_user):
    """Test admin login fails for non-admin user."""
    mock_cursor.fetchone.return_value = student_user

    payload = {"email": student_user["email"], "password": "studentpass123"}
    response = client.post("/auth/admin-login", data=payload)

    assert response.status_code == 200
    assert "Administrator access required" in response.text

def test_admin_login_invalid_email(client):
    """Test admin login fails for invalid email format."""
    payload = {"email": "not-an-email", "password": "password123"}
    response = client.post("/auth/admin-login", data=payload)

    assert response.status_code == 200
    assert "Invalid email format" in response.text
