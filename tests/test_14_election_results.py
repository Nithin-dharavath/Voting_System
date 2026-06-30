from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import jwt
from fastapi.testclient import TestClient

from app import COOKIE_NAME, CSRF_COOKIE_NAME, JWT_ALGORITHM, JWT_SECRET, app

client = TestClient(app)


def make_token(user_id: int = 2, role: str = "STUDENT", email: str = "student@example.com") -> str:
    payload = {
        "user_id": user_id,
        "role": role,
        "email": email,
        "exp": datetime.now(UTC) + timedelta(hours=24),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def admin_token(user_id: int = 1, email: str = "admin@college.edu") -> str:
    return make_token(user_id=user_id, role="ADMIN", email=email)


def student_token(user_id: int = 2, email: str = "student@example.com") -> str:
    return make_token(user_id=user_id, role="STUDENT", email=email)


def csrf_token() -> str:
    return "test-csrf-token"


def make_election(
    election_id: int = 10, status: str = "ENDED", result_published: bool = False
) -> dict:
    return {
        "id": election_id,
        "title": "Cultural Fest Lead 2025",
        "description": "Election for the Cultural Fest Lead.",
        "start_time": datetime.now(UTC) - timedelta(days=2),
        "end_time": datetime.now(UTC) - timedelta(days=1),
        "status": status,
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
# Admin: GET /admin/elections/{id}/results
# ---------------------------------------------------------------------------


def test_admin_results_page_unauthenticated_redirects():
    response = client.get("/admin/elections/10/results", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/login"


@patch("app.get_election_results")
@patch("app.get_election_by_id")
def test_admin_results_page_for_ended_election_returns_200(mock_get_election, mock_get_results):
    mock_get_election.return_value = make_election(status="ENDED", result_published=False)
    mock_get_results.return_value = (make_results(), 5)

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, admin_token())
    response = client.get("/admin/elections/10/results")

    assert response.status_code == 200
    body = response.text
    assert "Alice Student" in body
    assert "Bob Student" in body
    assert "Transparency first." in body
    assert "60.0%" in body
    assert "40.0%" in body
    assert "Total votes cast" in body
    assert "Publish Results" in body


@patch("app.get_election_by_id")
def test_admin_results_page_redirects_when_not_ended(mock_get_election):
    mock_get_election.return_value = make_election(status="ACTIVE", result_published=False)

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, admin_token())
    response = client.get("/admin/elections/10/results", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/admin/elections/10"


@patch("app.get_election_by_id")
def test_admin_results_page_redirects_when_election_missing(mock_get_election):
    mock_get_election.return_value = None

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, admin_token())
    response = client.get("/admin/elections/10/results", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/admin/elections"


@patch("app.get_election_results")
@patch("app.get_election_by_id")
def test_admin_results_page_hides_publish_button_when_published(
    mock_get_election, mock_get_results
):
    mock_get_election.return_value = make_election(status="ENDED", result_published=True)
    mock_get_results.return_value = (make_results(), 5)

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, admin_token())
    response = client.get("/admin/elections/10/results")

    assert response.status_code == 200
    body = response.text
    assert "Results Published" in body
    assert 'action="/admin/elections/10/publish-results"' not in body
    assert "publish-results" not in body.lower().replace("results published", "")


@patch("app.get_election_results")
@patch("app.get_election_by_id")
def test_admin_results_page_shows_info_message_after_publishing(
    mock_get_election, mock_get_results
):
    mock_get_election.return_value = make_election(status="ENDED", result_published=True)
    mock_get_results.return_value = (make_results(), 5)

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, admin_token())
    response = client.get("/admin/elections/10/results?success=published")

    assert response.status_code == 200
    assert "Results have been published to students." in response.text


# ---------------------------------------------------------------------------
# Admin: POST /admin/elections/{id}/publish-results
# ---------------------------------------------------------------------------


@patch("services.election_service.get_election_by_id")
def test_publish_results_sets_flag_and_redirects(mock_get_election, mock_cursor):
    mock_get_election.return_value = make_election(status="ENDED", result_published=False)

    token = csrf_token()
    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, admin_token())
    client.cookies.set(CSRF_COOKIE_NAME, token)

    response = client.post(
        "/admin/elections/10/publish-results",
        data={"csrf_token": token},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/elections/10/results?success=published"
    mock_cursor.execute.assert_called_once()
    sql = mock_cursor.execute.call_args[0][0]
    assert "UPDATE elections SET result_published = 1" in sql
    assert mock_cursor.execute.call_args[0][1] == (10,)


@patch("services.election_service.get_election_by_id")
def test_publish_results_rejects_non_ended_election(mock_get_election, mock_cursor):
    mock_get_election.return_value = make_election(status="ACTIVE", result_published=False)

    token = csrf_token()
    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, admin_token())
    client.cookies.set(CSRF_COOKIE_NAME, token)

    response = client.post(
        "/admin/elections/10/publish-results",
        data={"csrf_token": token},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/elections"
    mock_cursor.execute.assert_not_called()


@patch("services.election_service.get_election_by_id")
def test_publish_results_is_idempotent_when_already_published(mock_get_election, mock_cursor):
    mock_get_election.return_value = make_election(status="ENDED", result_published=True)

    token = csrf_token()
    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, admin_token())
    client.cookies.set(CSRF_COOKIE_NAME, token)

    response = client.post(
        "/admin/elections/10/publish-results",
        data={"csrf_token": token},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/elections/10/results?success=published"
    mock_cursor.execute.assert_not_called()


@patch("app.get_election_by_id")
def test_publish_results_redirects_when_election_missing(mock_get_election):
    mock_get_election.return_value = None

    token = csrf_token()
    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, admin_token())
    client.cookies.set(CSRF_COOKIE_NAME, token)

    response = client.post(
        "/admin/elections/10/publish-results",
        data={"csrf_token": token},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/elections"


# ---------------------------------------------------------------------------
# Student: GET /student/elections/{id}/results
# ---------------------------------------------------------------------------


def test_student_results_page_unauthenticated_redirects():
    response = client.get("/student/elections/10/results", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


@patch("app.get_election_results")
@patch("app.get_election_by_id")
def test_student_results_page_returns_200_when_published(mock_get_election, mock_get_results):
    mock_get_election.return_value = make_election(status="ENDED", result_published=True)
    mock_get_results.return_value = (make_results(), 5)

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, student_token())
    response = client.get("/student/elections/10/results")

    assert response.status_code == 200
    body = response.text
    assert "Alice Student" in body
    assert "Bob Student" in body
    assert "Transparency first." in body
    assert "60.0%" in body
    assert "40.0%" in body
    assert "5 votes were cast" in body


@patch("app.get_election_by_id")
def test_student_results_page_redirects_when_not_published(mock_get_election):
    mock_get_election.return_value = make_election(status="ENDED", result_published=False)

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, student_token())
    response = client.get("/student/elections/10/results", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/student/elections/10?info=not_published"


@patch("app.get_election_by_id")
def test_student_results_page_404s_when_election_missing(mock_get_election):
    mock_get_election.return_value = None

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, student_token())
    response = client.get("/student/elections/10/results", follow_redirects=False)

    assert response.status_code == 404


@patch("app.get_election_by_id")
def test_student_results_page_redirects_when_not_ended(mock_get_election):
    mock_get_election.return_value = make_election(status="ACTIVE", result_published=True)

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, student_token())
    response = client.get("/student/elections/10/results", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/student/elections/10?info=not_published"


@patch("app.get_election_results")
@patch("app.get_election_by_id")
def test_student_results_page_handles_singular_vote_text(mock_get_election, mock_get_results):
    mock_get_election.return_value = make_election(status="ENDED", result_published=True)
    mock_get_results.return_value = (
        [
            {
                "candidate_application_id": 101,
                "candidate_name": "Alice Student",
                "department": "Computer Science",
                "academic_year": "2025-26",
                "manifesto": "Only one vote.",
                "vote_count": 1,
                "percentage": 100.0,
            }
        ],
        1,
    )

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, student_token())
    response = client.get("/student/elections/10/results")

    assert response.status_code == 200
    assert "1 vote was cast" in response.text


# ---------------------------------------------------------------------------
# Student detail page gating (template-level)
# ---------------------------------------------------------------------------


@patch("app.get_election_by_id")
@patch("app.has_user_voted")
@patch("app.has_user_applied")
def test_student_detail_page_shows_view_results_when_published(
    mock_applied, mock_voted, mock_get_election
):
    mock_get_election.return_value = make_election(status="ENDED", result_published=True)
    mock_voted.return_value = False
    mock_applied.return_value = False

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, student_token())
    response = client.get("/student/elections/10")

    assert response.status_code == 200
    assert "/student/elections/10/results" in response.text
    assert "View Results" in response.text
    assert "Results pending publication" not in response.text
    assert "/student/results/" not in response.text


@patch("app.get_election_by_id")
@patch("app.has_user_voted")
@patch("app.has_user_applied")
def test_student_detail_page_hides_view_results_when_not_published(
    mock_applied, mock_voted, mock_get_election
):
    mock_get_election.return_value = make_election(status="ENDED", result_published=False)
    mock_voted.return_value = False
    mock_applied.return_value = False

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, student_token())
    response = client.get("/student/elections/10")

    assert response.status_code == 200
    assert "/student/elections/10/results" not in response.text
    assert "Results pending publication" in response.text


@patch("app.get_election_by_id")
@patch("app.has_user_voted")
@patch("app.has_user_applied")
def test_student_detail_page_renders_info_banner_on_not_published_redirect(
    mock_applied, mock_voted, mock_get_election
):
    mock_get_election.return_value = make_election(status="ENDED", result_published=False)
    mock_voted.return_value = False
    mock_applied.return_value = False

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, student_token())
    response = client.get("/student/elections/10?info=not_published")

    assert response.status_code == 200
    assert "The results for this election have not been published yet." in response.text
