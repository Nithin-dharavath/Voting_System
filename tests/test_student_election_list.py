from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

from app import COOKIE_NAME, JWT_ALGORITHM, JWT_SECRET, app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def student_user():
    return {"id": 1, "email": "student@example.com", "role": "STUDENT"}


@pytest.fixture
def admin_user():
    return {"id": 2, "email": "admin@example.com", "role": "ADMIN"}


def create_test_token(user_data):
    payload = {"user_id": user_data["id"], "role": user_data["role"], "email": user_data["email"]}
    expire = datetime.now(UTC) + timedelta(hours=24)
    payload.update({"exp": expire})
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def test_student_elections_unauthenticated(client):
    """Test that accessing /student/elections without authentication redirects to /login."""
    response = client.get("/student/elections", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


def test_student_elections_authenticated_success(client, mock_cursor, student_user):
    """Test that an authenticated student can view the list of elections."""
    token = create_test_token(student_user)
    client.cookies.set(COOKIE_NAME, token)

    # Mock a list of elections with different statuses
    mock_elections = [
        {
            "id": 101,
            "title": "Student Council 2026",
            "description": "Main council election",
            "start_time": datetime(2026, 6, 1, 10, 0),
            "end_time": datetime(2026, 6, 1, 18, 0),
            "status": "UPCOMING",
            "result_published": 0,
        },
        {
            "id": 102,
            "title": "Department Rep",
            "description": "Rep for Computer Science",
            "start_time": datetime(2026, 5, 1, 10, 0),
            "end_time": datetime(2026, 5, 1, 18, 0),
            "status": "ACTIVE",
            "result_published": 0,
        },
        {
            "id": 103,
            "title": "Club President",
            "description": "Annual club election",
            "start_time": datetime(2026, 4, 1, 10, 0),
            "end_time": datetime(2026, 4, 1, 18, 0),
            "status": "ENDED",
            "result_published": 0,
        },
    ]
    mock_cursor.fetchall.return_value = mock_elections

    response = client.get("/student/elections")
    assert response.status_code == 200

    # Check for titles and descriptions
    assert "Student Council 2026" in response.text
    assert "Main council election" in response.text
    assert "Department Rep" in response.text
    assert "Rep for Computer Science" in response.text
    assert "Club President" in response.text
    assert "Annual club election" in response.text

    # Check for links to detail pages
    assert "/student/elections/101" in response.text
    assert "/student/elections/102" in response.text
    assert "/student/elections/103" in response.text


def test_student_elections_empty_list(client, mock_cursor, student_user):
    """Test the student elections page when no elections exist."""
    token = create_test_token(student_user)
    client.cookies.set(COOKIE_NAME, token)

    mock_cursor.fetchall.return_value = []

    response = client.get("/student/elections")
    assert response.status_code == 200
    # The template should handle empty lists gracefully.
    # Since we don't have the template, we just verify it loads.


def test_student_elections_admin_access_forbidden(client, admin_user):
    """Test that an admin user is redirected if they try to access the student elections list."""
    token = create_test_token(admin_user)
    client.cookies.set(COOKIE_NAME, token)

    response = client.get("/student/elections", follow_redirects=False)
    # student_guard redirects non-STUDENTs to /login
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


def test_student_access_admin_route_forbidden(client, student_user):
    """Test that a student user cannot access admin routes."""
    token = create_test_token(student_user)
    client.cookies.set(COOKIE_NAME, token)

    response = client.get("/admin/dashboard", follow_redirects=False)
    # admin_guard redirects non-ADMINs to /admin/login
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/login"
