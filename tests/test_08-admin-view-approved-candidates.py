import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app import app, JWT_SECRET, JWT_ALGORITHM, COOKIE_NAME, CSRF_COOKIE_NAME
import jwt
from datetime import datetime, timedelta, timezone

client = TestClient(app)

# --- Helpers ---

def create_test_token(user_id: int, role: str, email: str):
    payload = {
        "user_id": user_id,
        "role": role,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_admin_cookies():
    token = create_test_token(1, "ADMIN", "admin@example.com")
    return {COOKIE_NAME: token}

def get_student_cookies():
    token = create_test_token(2, "STUDENT", "student@example.com")
    return {COOKIE_NAME: token}

# --- Tests ---

@patch("app.get_db_cursor")
def test_get_approved_candidates_admin(mock_cursor):
    """
    Happy path: Admin accessing /admin/candidates/approved and seeing approved candidates.
    """
    mock_cur = MagicMock()
    mock_cur.fetchall.return_value = [
        {
            "id": 1,
            "user_id": 2,
            "election_id": 10,
            "manifesto": "My manifesto",
            "approval_status": "APPROVED",
            "applied_at": datetime.now(),
            "applicant_name": "Approved Student",
            "election_title": "School Council 2026"
        },
        {
            "id": 2,
            "user_id": 3,
            "election_id": 10,
            "manifesto": "Another manifesto",
            "approval_status": "APPROVED",
            "applied_at": datetime.now(),
            "applicant_name": "Another Approved Student",
            "election_title": "School Council 2026"
        }
    ]
    mock_cursor.return_value.__enter__.return_value = mock_cur

    cookies = get_admin_cookies()
    response = client.get("/admin/candidates/approved", cookies=cookies, follow_redirects=False)

    assert response.status_code == 200
    assert "Approved Student" in response.text
    assert "Another Approved Student" in response.text
    assert "School Council 2026" in response.text

def test_get_approved_candidates_non_admin():
    """
    Auth guard: Ensure the route is protected by admin_guard.
    """
    cookies = get_student_cookies()
    response = client.get("/admin/candidates/approved", cookies=cookies, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/login"

def test_get_approved_candidates_unauthenticated():
    """
    Auth guard: Ensure unauthenticated users are redirected to admin login.
    """
    response = client.get("/admin/candidates/approved", cookies={}, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/login"

@patch("app.get_db_cursor")
def test_get_approved_candidates_filtering(mock_cursor):
    """
    Filtering: Ensure only candidates with approval_status = 'APPROVED' are fetched.
    """
    mock_cur = MagicMock()
    mock_cur.fetchall.return_value = []
    mock_cursor.return_value.__enter__.return_value = mock_cur

    cookies = get_admin_cookies()
    client.get("/admin/candidates/approved", cookies=cookies)

    # Verify the SQL query uses 'APPROVED'
    called_query = mock_cur.execute.call_args[0][0]
    called_params = mock_cur.execute.call_args[0][1]

    assert "WHERE ca.approval_status = %s" in called_query
    assert "APPROVED" in called_params

@patch("app.get_db_cursor")
def test_admin_dashboard_link(mock_cursor):
    """
    Navigation: Check for the link to approved candidates in the admin dashboard.
    """
    # Mock the stats for the dashboard
    mock_cur = MagicMock()
    # Mock fetchone for the 3 count queries in admin_dashboard
    mock_cur.fetchone.side_effect = [
        {"count": 100}, # total_students
        {"count": 5},    # active_elections
        {"count": 10},   # pending_apps
    ]
    mock_cursor.return_value.__enter__.return_value = mock_cur

    cookies = get_admin_cookies()
    response = client.get("/admin/dashboard", cookies=cookies)

    assert response.status_code == 200
    assert '/admin/candidates/approved' in response.text
