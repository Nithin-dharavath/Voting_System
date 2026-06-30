from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import jwt
from fastapi.testclient import TestClient

from app import COOKIE_NAME, JWT_ALGORITHM, JWT_SECRET, app

client = TestClient(app)


def admin_token(user_id: int = 1, email: str = "admin@college.edu") -> str:
    payload = {
        "user_id": user_id,
        "role": "ADMIN",
        "email": email,
        "exp": datetime.now(UTC) + timedelta(hours=24),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def student_token(user_id: int = 2, email: str = "student@example.com") -> str:
    payload = {
        "user_id": user_id,
        "role": "STUDENT",
        "email": email,
        "exp": datetime.now(UTC) + timedelta(hours=24),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def make_ended_election(election_id: int = 10, result_published: bool = False) -> dict:
    return {
        "id": election_id,
        "title": f"Election {election_id}",
        "description": f"Description for election {election_id}",
        "start_time": datetime.now(UTC) - timedelta(days=3),
        "end_time": datetime.now(UTC) - timedelta(days=1),
        "status": "ENDED",
        "result_published": result_published,
    }


def make_results() -> list:
    return [
        {
            "candidate_application_id": 101,
            "candidate_name": "Alice Student",
            "department": "Computer Science",
            "academic_year": "2025-26",
            "manifesto": "Transparency first.",
            "vote_count": 3,
            "percentage": 60.0,
        },
        {
            "candidate_application_id": 102,
            "candidate_name": "Bob Student",
            "department": "Electrical Engineering",
            "academic_year": "2025-26",
            "manifesto": "Better facilities.",
            "vote_count": 2,
            "percentage": 40.0,
        },
    ]


# ---------------------------------------------------------------------------
# GET /admin/results
# ---------------------------------------------------------------------------


def test_admin_results_overview_unauthenticated_redirects():
    response = client.get("/admin/results", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/login"


def test_admin_results_overview_student_redirects():
    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, student_token())
    response = client.get("/admin/results", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/login"


@patch("services.election_service.get_election_results")
def test_admin_results_overview_renders_all_ended_elections(mock_get_results, mock_cursor):
    mock_cursor.fetchall.return_value = [
        make_ended_election(10, result_published=True),
        make_ended_election(11, result_published=False),
    ]
    mock_get_results.return_value = (make_results(), 5)

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, admin_token())
    response = client.get("/admin/results")

    assert response.status_code == 200
    body = response.text
    assert "Election 10" in body
    assert "Election 11" in body
    assert "Completed Elections" in body
    assert "Published" in body
    assert "Hidden" in body
    assert "Alice Student" in body
    assert "Bob Student" in body
    assert "60.0%" in body
    assert "View Full Details" in body
    assert 'action="/admin/elections/11/publish-results"' in body


@patch("services.election_service.get_election_results")
def test_admin_results_overview_hides_publish_when_already_published(mock_get_results, mock_cursor):
    mock_cursor.fetchall.return_value = [
        make_ended_election(10, result_published=True),
    ]
    mock_get_results.return_value = (make_results(), 5)

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, admin_token())
    response = client.get("/admin/results")

    assert response.status_code == 200
    body = response.text
    assert "publish-results" not in body.lower().replace("results published", "").replace(
        "published", ""
    )


@patch("services.election_service.get_election_results")
def test_admin_results_overview_shows_info_message_after_publish(mock_get_results, mock_cursor):
    mock_cursor.fetchall.return_value = [
        make_ended_election(10, result_published=True),
    ]
    mock_get_results.return_value = (make_results(), 5)

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, admin_token())
    response = client.get("/admin/results?success=published")

    assert response.status_code == 200
    assert "Results have been published to students." in response.text


@patch("services.election_service.get_election_results")
def test_admin_results_overview_empty_state_when_no_ended_elections(mock_get_results, mock_cursor):
    mock_cursor.fetchall.return_value = []
    mock_get_results.return_value = ([], 0)

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, admin_token())
    response = client.get("/admin/results")

    assert response.status_code == 200
    assert "No Completed Elections Yet" in response.text


@patch("services.election_service.get_election_results")
def test_admin_results_overview_highlights_winner(mock_get_results, mock_cursor):
    mock_cursor.fetchall.return_value = [
        make_ended_election(10, result_published=False),
    ]
    mock_get_results.return_value = (make_results(), 5)

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, admin_token())
    response = client.get("/admin/results")

    assert response.status_code == 200
    body = response.text
    assert "rank-winner" in body
    assert "winner-row" in body
    assert "results-bar-fill" in body
    assert "results-bar-fill winner" in body


# ---------------------------------------------------------------------------
# GET /student/results
# ---------------------------------------------------------------------------


def test_student_results_overview_unauthenticated_redirects():
    response = client.get("/student/results", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


def test_student_results_overview_admin_redirects():
    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, admin_token())
    response = client.get("/student/results", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


@patch("app.get_election_results")
def test_student_results_overview_filters_to_published_only(mock_get_results, mock_cursor):
    mock_cursor.fetchall.return_value = [
        make_ended_election(10, result_published=True),
    ]
    mock_get_results.return_value = (make_results(), 5)

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, student_token())
    response = client.get("/student/results")

    assert response.status_code == 200
    body = response.text
    assert "Election 10" in body
    assert "Alice Student" in body
    assert "60.0%" in body
    assert "View Full Results" in body
    assert "publish-results" not in body
    assert "Publish Results" not in body
    sql = mock_cursor.execute.call_args[0][0]
    assert "result_published = 1" in sql


@patch("app.get_election_results")
def test_student_results_overview_empty_state(mock_get_results, mock_cursor):
    mock_cursor.fetchall.return_value = []
    mock_get_results.return_value = ([], 0)

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, student_token())
    response = client.get("/student/results")

    assert response.status_code == 200
    assert "No Published Results Yet" in response.text


# ---------------------------------------------------------------------------
# Navbar / Sidebar presence
# ---------------------------------------------------------------------------


@patch("services.election_service.get_election_results")
def test_admin_navbar_contains_results_link(mock_get_results, mock_cursor):
    mock_cursor.fetchall.return_value = []
    mock_get_results.return_value = ([], 0)

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, admin_token())
    response = client.get("/admin/results")

    assert response.status_code == 200
    assert 'href="/admin/results"' in response.text
    assert "nav-results-link" in response.text


@patch("app.get_election_results")
def test_student_navbar_contains_results_link(mock_get_results, mock_cursor):
    mock_cursor.fetchall.return_value = []
    mock_get_results.return_value = ([], 0)

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, student_token())
    response = client.get("/student/results")

    assert response.status_code == 200
    assert 'href="/student/results"' in response.text
    assert "nav-results-link" in response.text


@patch("services.election_service.get_election_results")
def test_admin_sidebar_contains_results_link(mock_get_results, mock_cursor):
    mock_cursor.fetchall.return_value = []
    mock_get_results.return_value = ([], 0)

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, admin_token())
    response = client.get("/admin/results")

    assert response.status_code == 200
    body = response.text
    assert 'href="/admin/results"' in body
    assert body.count('href="/admin/results"') >= 2
    assert 'class="active"' in body
