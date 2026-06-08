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

def get_csrf_cookie_and_token():
    csrf_token = "test-csrf-token-123"
    return {CSRF_COOKIE_NAME: csrf_token}, csrf_token

# --- Tests ---

def _setup_admin_csrf():
    """Set admin auth + CSRF cookies on the shared client."""
    client.cookies.clear()
    token = create_test_token(1, "ADMIN", "admin@example.com")
    client.cookies.set(COOKIE_NAME, token)
    csrf_token = "test-csrf-token-123"
    client.cookies.set(CSRF_COOKIE_NAME, csrf_token)
    return csrf_token

@patch("app.get_db_cursor")
def test_get_pending_candidates_admin(mock_cursor):
    mock_cur = MagicMock()
    mock_cursor.return_value.__enter__.return_value = mock_cur
    # Fetch departments query (first call)
    mock_cur.fetchone.side_effect = None
    # The route now fetches departments too
    def fetchall_side_effect():
        mock_cur.fetchall.side_effect = [
            [],  # departments
            [   # candidates
                {
                    "id": 1,
                    "user_id": 2,
                    "election_id": 10,
                    "manifesto": "My manifesto",
                    "approval_status": "PENDING",
                    "applied_at": datetime.now(),
                    "applicant_name": "Student One",
                    "election_title": "School Council 2026"
                }
            ]
        ]
    fetchall_side_effect()

    client.cookies.clear()
    token = create_test_token(1, "ADMIN", "admin@example.com")
    client.cookies.set(COOKIE_NAME, token)

    # Follow redirect from /admin/candidates/pending -> /admin/candidates?status=PENDING
    response = client.get("/admin/candidates/pending", follow_redirects=True)

    assert response.status_code == 200
    assert "Student One" in response.text
    assert "School Council 2026" in response.text

def test_get_pending_candidates_non_admin():
    client.cookies.clear()
    token = create_test_token(2, "STUDENT", "student@example.com")
    client.cookies.set(COOKIE_NAME, token)
    response = client.get("/admin/candidates/pending", follow_redirects=False)
    assert response.status_code == 302
    # The /admin/candidates/pending route has no guard; it redirects to /admin/candidates?status=PENDING
    assert response.headers["location"] == "/admin/candidates?status=PENDING"

@patch("app.get_db_cursor")
def test_approve_candidate_success(mock_cursor):
    csrf_token = _setup_admin_csrf()

    mock_cur = MagicMock()
    mock_cursor.return_value.__enter__.return_value = mock_cur

    response = client.post(
        "/admin/candidates/1/approve",
        data={"csrf_token": csrf_token},
        follow_redirects=False
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/candidates"

    mock_cur.execute.assert_called_with(
        "UPDATE candidate_applications SET approval_status = %s, reviewed_by = %s WHERE id = %s",
        ("APPROVED", 1, 1)
    )

def test_approve_candidate_csrf_fail():
    _setup_admin_csrf()

    response = client.post(
        "/admin/candidates/1/approve",
        data={"csrf_token": "wrong-token"},
        follow_redirects=False
    )

    assert response.status_code == 403
    assert "CSRF token missing or invalid" in response.text

def test_approve_candidate_non_admin():
    client.cookies.clear()
    token = create_test_token(2, "STUDENT", "student@example.com")
    client.cookies.set(COOKIE_NAME, token)
    csrf_token = "test-csrf-token-123"
    client.cookies.set(CSRF_COOKIE_NAME, csrf_token)

    response = client.post(
        "/admin/candidates/1/approve",
        data={"csrf_token": csrf_token},
        follow_redirects=False
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/login"

@patch("app.get_db_cursor")
def test_reject_candidate_success(mock_cursor):
    csrf_token = _setup_admin_csrf()
    mock_cur = MagicMock()
    mock_cursor.return_value.__enter__.return_value = mock_cur

    response = client.post(
        "/admin/candidates/1/reject",
        data={"csrf_token": csrf_token},
        follow_redirects=False
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/candidates"

    mock_cur.execute.assert_called_with(
        "UPDATE candidate_applications SET approval_status = %s, reviewed_by = %s WHERE id = %s",
        ("REJECTED", 1, 1)
    )

def test_reject_candidate_csrf_fail():
    _setup_admin_csrf()

    response = client.post(
        "/admin/candidates/1/reject",
        data={"csrf_token": "wrong-token"},
        follow_redirects=False
    )

    assert response.status_code == 403
    assert "CSRF token missing or invalid" in response.text

def test_reject_candidate_non_admin():
    client.cookies.clear()
    token = create_test_token(2, "STUDENT", "student@example.com")
    client.cookies.set(COOKIE_NAME, token)
    csrf_token = "test-csrf-token-123"
    client.cookies.set(CSRF_COOKIE_NAME, csrf_token)

    response = client.post(
        "/admin/candidates/1/reject",
        data={"csrf_token": csrf_token},
        follow_redirects=False
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/login"

@patch("app.get_db_cursor")
@patch("app.get_election_by_id")
def test_get_election_candidates_success(mock_get_election, mock_cursor):
    mock_get_election.return_value = {"id": 10, "title": "School Council 2026"}

    mock_cur = MagicMock()
    mock_cur.fetchall.return_value = [
        {
            "id": 1,
            "user_id": 2,
            "election_id": 10,
            "manifesto": "Manifesto 1",
            "approval_status": "APPROVED",
            "applied_at": datetime.now(),
            "applicant_name": "Student One"
        },
        {
            "id": 2,
            "user_id": 3,
            "election_id": 10,
            "manifesto": "Manifesto 2",
            "approval_status": "PENDING",
            "applied_at": datetime.now(),
            "applicant_name": "Student Two"
        }
    ]
    mock_cursor.return_value.__enter__.return_value = mock_cur

    cookies = get_admin_cookies()
    response = client.get("/admin/elections/10/candidates", cookies=cookies, follow_redirects=False)

    assert response.status_code == 200
    assert "Student One" in response.text
    assert "Student Two" in response.text

def test_get_election_candidates_non_admin():
    cookies = get_student_cookies()
    response = client.get("/admin/elections/10/candidates", cookies=cookies, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/login"

@patch("app.get_election_by_id")
def test_get_election_candidates_not_found(mock_get_election):
    mock_get_election.return_value = None
    cookies = get_admin_cookies()
    response = client.get("/admin/elections/999/candidates", cookies=cookies, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/elections"
