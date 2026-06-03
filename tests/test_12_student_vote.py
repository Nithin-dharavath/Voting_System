from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import jwt
from fastapi.testclient import TestClient

from app import app, COOKIE_NAME, CSRF_COOKIE_NAME, JWT_ALGORITHM, JWT_SECRET

client = TestClient(app)


def create_test_token(user_id: int = 2, role: str = "STUDENT", email: str = "student@example.com"):
    payload = {
        "user_id": user_id,
        "role": role,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def student_cookies():
    return {COOKIE_NAME: create_test_token()}


def csrf_cookies(token: str = "test-csrf-token"):
    return {CSRF_COOKIE_NAME: token}


@patch("app.get_election_by_id")
def test_vote_page_redirects_unauthenticated(mock_get_election):
    mock_get_election.return_value = {
        "id": 10,
        "title": "Student Council",
        "description": "Campus leadership election",
        "start_time": datetime.now(),
        "end_time": datetime.now() + timedelta(hours=2),
        "status": "ACTIVE",
    }

    response = client.get("/student/elections/10/vote", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


@patch("app.get_election_by_id")
@patch("app.has_user_voted")
@patch("app.get_approved_candidates_for_election")
def test_vote_page_shows_approved_candidates(mock_candidates, mock_has_voted, mock_get_election):
    mock_get_election.return_value = {
        "id": 10,
        "title": "Student Council",
        "description": "Campus leadership election",
        "start_time": datetime.now(),
        "end_time": datetime.now() + timedelta(hours=2),
        "status": "ACTIVE",
    }
    mock_has_voted.return_value = False
    mock_candidates.return_value = [
        {
            "id": 101,
            "user_id": 2,
            "election_id": 10,
            "manifesto": "Transparency first.",
            "candidate_name": "Alice Student",
            "department": "Computer Science",
            "academic_year": "2025-26",
        }
    ]

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, create_test_token())
    response = client.get("/student/elections/10/vote")

    assert response.status_code == 200
    assert "Alice Student" in response.text
    assert "Transparency first." in response.text
    assert "/student/elections/10/vote" in response.text


@patch("app.get_election_by_id")
def test_vote_page_rejects_non_active_election(mock_get_election):
    mock_get_election.return_value = {
        "id": 10,
        "title": "Student Council",
        "description": "Campus leadership election",
        "start_time": datetime.now(),
        "end_time": datetime.now() + timedelta(hours=2),
        "status": "UPCOMING",
    }

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, create_test_token())
    response = client.get("/student/elections/10/vote", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/student/elections/10?error=inactive"


@patch("app.get_election_by_id")
@patch("app.has_user_voted")
@patch("app.get_approved_candidate_for_vote")
@patch("app.mark_voting_session_completed")
@patch("app.get_db_cursor")
def test_submit_vote_success(
    mock_get_db_cursor,
    mock_mark_session,
    mock_get_candidate,
    mock_has_voted,
    mock_get_election,
):
    mock_get_election.return_value = {
        "id": 10,
        "title": "Student Council",
        "description": "Campus leadership election",
        "start_time": datetime.now(),
        "end_time": datetime.now() + timedelta(hours=2),
        "status": "ACTIVE",
    }
    mock_has_voted.return_value = False
    mock_get_candidate.return_value = {
        "id": 101,
        "user_id": 2,
        "election_id": 10,
        "approval_status": "APPROVED",
    }

    mock_cm = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db_cursor.return_value = mock_cm
    mock_cm.__enter__.return_value = mock_cursor

    csrf_token = "test-csrf-token"
    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, create_test_token())
    client.cookies.set(CSRF_COOKIE_NAME, csrf_token)

    response = client.post(
        "/student/elections/10/vote",
        data={"csrf_token": csrf_token, "candidate_application_id": 101},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/student/elections/10?success=voted"
    mock_cursor.execute.assert_called_once()
    mock_mark_session.assert_called_once_with(2, 10)


@patch("app.get_election_by_id")
@patch("app.has_user_voted")
@patch("app.get_approved_candidate_for_vote")
def test_submit_vote_rejects_invalid_candidate(
    mock_get_candidate,
    mock_has_voted,
    mock_get_election,
):
    mock_get_election.return_value = {
        "id": 10,
        "title": "Student Council",
        "description": "Campus leadership election",
        "start_time": datetime.now(),
        "end_time": datetime.now() + timedelta(hours=2),
        "status": "ACTIVE",
    }
    mock_has_voted.return_value = False
    mock_get_candidate.return_value = None

    csrf_token = "test-csrf-token"
    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, create_test_token())
    client.cookies.set(CSRF_COOKIE_NAME, csrf_token)

    response = client.post(
        "/student/elections/10/vote",
        data={"csrf_token": csrf_token, "candidate_application_id": 999},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/student/elections/10/vote?error=invalid_candidate"


@patch("app.get_election_by_id")
@patch("app.has_user_voted")
def test_detail_page_hides_vote_action_after_vote(mock_has_voted, mock_get_election):
    mock_get_election.return_value = {
        "id": 10,
        "title": "Student Council",
        "description": "Campus leadership election",
        "start_time": datetime.now(),
        "end_time": datetime.now() + timedelta(hours=2),
        "status": "ACTIVE",
    }
    mock_has_voted.return_value = True

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, create_test_token())
    response = client.get("/student/elections/10")

    assert response.status_code == 200
    assert "Vote already recorded" in response.text
    assert "Vote Now" not in response.text
