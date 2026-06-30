from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from werkzeug.security import generate_password_hash

from app import app
from services.auth_service import COOKIE_NAME, JWT_ALGORITHM, get_jwt_secret


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def student_user():
    return {
        "user_id": 1,
        "email": "student@example.com",
        "password_hash": generate_password_hash("studentpass123"),
        "role": "STUDENT",
    }


@pytest.fixture
def admin_user():
    return {
        "user_id": 2,
        "email": "admin@example.com",
        "password_hash": generate_password_hash("adminpass123"),
        "role": "ADMIN",
    }


def create_test_token(user_data):
    payload = {
        "user_id": user_data["user_id"],
        "role": user_data["role"],
        "email": user_data["email"],
    }
    expire = datetime.now(UTC) + timedelta(hours=24)
    payload.update({"exp": expire})
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)


def test_login_page_success(client):
    response = client.get("/login")
    assert response.status_code == 200


def test_admin_login_page_success(client):
    response = client.get("/admin/login")
    assert response.status_code == 200


def test_student_login_success(client, mock_cursor, student_user):
    mock_cursor.fetchone.return_value = student_user
    payload = {"email": student_user["email"], "password": "studentpass123"}
    response = client.post("/auth/login", data=payload, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/student/dashboard?login=success"
    cookie = response.cookies.get(COOKIE_NAME)
    assert cookie is not None


def test_admin_login_via_admin_route_success(client, mock_cursor, admin_user):
    mock_cursor.fetchone.return_value = admin_user
    payload = {"email": admin_user["email"], "password": "adminpass123"}
    response = client.post("/auth/admin-login", data=payload, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/dashboard?login=success"


def test_login_invalid_credentials(client, mock_cursor):
    mock_cursor.fetchone.return_value = None
    payload = {"email": "nonexistent@example.com", "password": "password123"}
    response = client.post("/auth/login", data=payload)
    assert response.status_code == 200
    assert "Invalid email or password" in response.text


def test_login_wrong_password(client, mock_cursor, student_user):
    mock_cursor.fetchone.return_value = student_user
    payload = {"email": student_user["email"], "password": "wrongpassword"}
    response = client.post("/auth/login", data=payload)
    assert response.status_code == 200
    assert "Invalid email or password" in response.text


def test_admin_login_role_mismatch(client, mock_cursor, student_user):
    mock_cursor.fetchone.return_value = student_user
    payload = {"email": student_user["email"], "password": "studentpass123"}
    response = client.post("/auth/admin-login", data=payload)
    assert response.status_code == 200
    assert "Administrator access required" in response.text


def test_protected_route_no_auth(client):
    response = client.get("/student/dashboard", follow_redirects=False)
    assert response.status_code in (307, 302)
    assert response.headers["location"] == "/login"

    response = client.get("/admin/dashboard", follow_redirects=False)
    assert response.status_code in (307, 302)
    assert response.headers["location"] == "/admin/login"


def test_student_dashboard_admin_token(client, admin_user):
    token = create_test_token(admin_user)
    client.cookies.set(COOKIE_NAME, token)
    response = client.get("/student/dashboard", follow_redirects=False)
    assert response.status_code in (307, 302)
    assert response.headers["location"] == "/login"


def test_admin_dashboard_student_token(client, student_user):
    token = create_test_token(student_user)
    client.cookies.set(COOKIE_NAME, token)
    response = client.get("/admin/dashboard", follow_redirects=False)
    assert response.status_code in (307, 302)
    assert response.headers["location"] == "/admin/login"


def test_logout_success(client, mock_cursor, student_user):
    mock_cursor.fetchone.return_value = student_user
    payload = {"email": student_user["email"], "password": "studentpass123"}
    client.post("/auth/login", data=payload)
    response = client.get("/auth/logout", follow_redirects=True)
    assert response.status_code == 200
    assert COOKIE_NAME not in client.cookies


def test_authenticated_redirects_login_page(client, student_user):
    token = create_test_token(student_user)
    client.cookies.set(COOKIE_NAME, token)
    response = client.get("/login", follow_redirects=False)
    assert response.status_code in (307, 302)
    assert response.headers["location"] == "/student/dashboard"
