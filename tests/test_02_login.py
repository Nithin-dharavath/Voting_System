import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from werkzeug.security import generate_password_hash
from app import app, JWT_SECRET, JWT_ALGORITHM, COOKIE_NAME
import jwt

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

def create_test_token(user_data):
    payload = {
        "user_id": user_data["user_id"],
        "role": user_data["role"],
        "email": user_data["email"]
    }
    from datetime import datetime, timedelta, timezone
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    payload.update({"exp": expire})
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def test_login_page_success(client):
    """Test that GET /login renders the login form."""
    response = client.get("/login")
    assert response.status_code == 200

def test_admin_login_page_success(client):
    """Test that GET /admin/login renders the admin login form."""
    response = client.get("/admin/login")
    assert response.status_code == 200

def test_student_login_success(client, mock_cursor, student_user):
    """Test successful student login."""
    mock_cursor.fetchone.return_value = student_user

    payload = {
        "email": student_user["email"],
        "password": "studentpass123"
    }

    response = client.post("/auth/login", data=payload, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/student/dashboard?login=success"
    cookie = response.cookies.get(COOKIE_NAME)
    assert cookie is not None

def test_admin_login_success(client, mock_cursor, admin_user):
    """Test successful admin login via /auth/login."""
    mock_cursor.fetchone.return_value = admin_user

    payload = {
        "email": admin_user["email"],
        "password": "adminpass123"
    }

    response = client.post("/auth/login", data=payload, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/dashboard?login=success"
    assert client.cookies.get(COOKIE_NAME) is not None

def test_admin_login_via_admin_route_success(client, mock_cursor, admin_user):
    """Test successful admin login via /auth/admin-login."""
    mock_cursor.fetchone.return_value = admin_user

    payload = {
        "email": admin_user["email"],
        "password": "adminpass123"
    }

    response = client.post("/auth/admin-login", data=payload, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/dashboard?login=success"

def test_login_invalid_credentials(client, mock_cursor):
    """Test login fails with invalid credentials."""
    mock_cursor.fetchone.return_value = None

    payload = {"email": "nonexistent@example.com", "password": "password123"}
    response = client.post("/auth/login", data=payload)
    assert response.status_code == 200
    assert "Invalid email or password" in response.text

def test_login_wrong_password(client, mock_cursor, student_user):
    """Test login fails with wrong password."""
    mock_cursor.fetchone.return_value = student_user

    payload = {"email": student_user["email"], "password": "wrongpassword"}
    response = client.post("/auth/login", data=payload)
    assert response.status_code == 200
    assert "Invalid email or password" in response.text

def test_admin_login_role_mismatch(client, mock_cursor, student_user):
    """Test admin login fails for non-admin user."""
    mock_cursor.fetchone.return_value = student_user

    payload = {"email": student_user["email"], "password": "studentpass123"}
    response = client.post("/auth/admin-login", data=payload)

    assert response.status_code == 200
    assert "Administrator access required" in response.text

def test_protected_route_no_auth(client):
    """Test that accessing protected routes without auth redirects to login."""
    # Student dashboard
    response = client.get("/student/dashboard", follow_redirects=False)
    assert response.status_code == 307 or response.status_code == 302
    assert response.headers["location"] == "/login"

    # Admin dashboard
    response = client.get("/admin/dashboard", follow_redirects=False)
    assert response.status_code == 307 or response.status_code == 302
    assert response.headers["location"] == "/admin/login"

def test_student_dashboard_admin_token(client, admin_user):
    """Test that an admin cannot access student dashboard."""
    token = create_test_token(admin_user)
    client.cookies.set(COOKIE_NAME, token)

    response = client.get("/student/dashboard", follow_redirects=False)
    assert response.status_code == 307 or response.status_code == 302
    assert response.headers["location"] == "/login"

def test_admin_dashboard_student_token(client, student_user):
    """Test that a student cannot access admin dashboard."""
    token = create_test_token(student_user)
    client.cookies.set(COOKIE_NAME, token)

    response = client.get("/admin/dashboard", follow_redirects=False)
    assert response.status_code == 307 or response.status_code == 302
    assert response.headers["location"] == "/admin/login"

def test_logout_success(client, mock_cursor, student_user):
    """Test that logout removes the session cookie."""
    # First, log in to get a real cookie
    mock_cursor.fetchone.return_value = student_user
    payload = {"email": student_user["email"], "password": "studentpass123"}
    client.post("/auth/login", data=payload)

    assert COOKIE_NAME in client.cookies

    response = client.get("/auth/logout", follow_redirects=True)
    assert response.status_code == 200
    assert COOKIE_NAME not in client.cookies

def test_authenticated_redirects_login_page(client, student_user):
    """Test that authenticated users are redirected away from login page."""
    token = create_test_token(student_user)
    client.cookies.set(COOKIE_NAME, token)

    response = client.get("/login", follow_redirects=False)
    assert response.status_code == 307 or response.status_code == 302
    assert response.headers["location"] == "/student/dashboard"

def test_authenticated_redirects_register_page(client, admin_user):
    """Test that authenticated users are redirected away from register page."""
    token = create_test_token(admin_user)
    client.cookies.set(COOKIE_NAME, token)

    response = client.get("/register", follow_redirects=False)
    assert response.status_code == 307 or response.status_code == 302
    assert response.headers["location"] == "/admin/dashboard"

def test_invalid_email_format(client):
    """Test login fails for invalid email format."""
    payload = {"email": "not-an-email", "password": "password123"}
    response = client.post("/auth/login", data=payload)
    assert response.status_code == 200
    assert "Invalid email format" in response.text