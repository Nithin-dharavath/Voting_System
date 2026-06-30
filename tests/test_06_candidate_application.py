import re
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app import COOKIE_NAME, app, create_access_token
from database.connection import get_db_cursor

client = TestClient(app)


def get_student_token(user_id=1, email="student@example.com"):
    return create_access_token({"user_id": user_id, "role": "STUDENT", "email": email})


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    """Clean up and set up the database for each test."""
    now = datetime.now(UTC)
    with get_db_cursor() as cursor:
        # Clear existing applications for the test user/election
        cursor.execute("DELETE FROM candidate_applications")
        # Ensure we have a test student
        cursor.execute(
            "INSERT IGNORE INTO users (user_id, full_name, email, password_hash, department, academic_year, role) VALUES (1, 'Test Student', 'student@example.com', 'hashed_pw', 'CS', '2023', 'STUDENT')"
        )
        # Ensure we have test elections with relative dates
        cursor.execute("DELETE FROM elections WHERE id IN (1, 2, 3)")
        cursor.execute(
            "INSERT INTO elections (id, title, description, start_time, end_time) VALUES (1, 'Upcoming Election', 'Desc', %s, %s)",
            (now + timedelta(days=7), now + timedelta(days=8)),
        )
        cursor.execute(
            "INSERT INTO elections (id, title, description, start_time, end_time) VALUES (2, 'Active Election', 'Desc', %s, %s)",
            (now - timedelta(days=1), now + timedelta(days=1)),
        )
        cursor.execute(
            "INSERT INTO elections (id, title, description, start_time, end_time) VALUES (3, 'Ended Election', 'Desc', %s, %s)",
            (now - timedelta(days=90), now - timedelta(days=89)),
        )
    yield


def test_apply_page_upcoming_election():
    """Test that students can access the apply page for UPCOMING elections."""
    token = get_student_token()
    response = client.get("/student/elections/1/apply", cookies={COOKIE_NAME: token})
    assert response.status_code == 200


def test_apply_page_active_election():
    """Test that students cannot access the apply page for ACTIVE elections."""
    token = get_student_token()
    response = client.get(
        "/student/elections/2/apply", cookies={COOKIE_NAME: token}, follow_redirects=False
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/student/elections"


def test_apply_page_ended_election():
    """Test that students cannot access the apply page for ENDED elections."""
    token = get_student_token()
    response = client.get(
        "/student/elections/3/apply", cookies={COOKIE_NAME: token}, follow_redirects=False
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/student/elections"


def test_apply_page_already_applied():
    """Test that students are redirected if they have already applied."""
    token = get_student_token()
    with get_db_cursor() as cursor:
        cursor.execute(
            "INSERT INTO candidate_applications (user_id, election_id, manifesto, approval_status) VALUES (1, 1, 'My Manifesto', 'PENDING')"
        )

    response = client.get(
        "/student/elections/1/apply", cookies={COOKIE_NAME: token}, follow_redirects=False
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/student/candidate-status"


def test_apply_page_unauthenticated():
    """Test that unauthenticated users are redirected to login."""
    response = client.get("/student/elections/1/apply", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["location"]


def test_submit_application_success():
    """Test successful submission of candidate application."""
    token = get_student_token()
    res = client.get("/student/elections/1/apply", cookies={COOKIE_NAME: token})
    csrf_token = res.cookies.get("csrf_token")
    if not csrf_token:
        match = re.search(r'name="csrf_token" value="([^"]+)"', res.text)
        csrf_token = match.group(1) if match else None

    data = {
        "election_id": 1,
        "manifesto": "I will bring positive change to the campus!",
        "csrf_token": csrf_token,
    }
    cookies = {COOKIE_NAME: token, "csrf_token": csrf_token}
    response = client.post("/candidates/apply", data=data, cookies=cookies, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/student/candidate-status"

    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT id, approval_status FROM candidate_applications WHERE user_id = 1 AND election_id = 1"
        )
        row = cursor.fetchone()
        assert row is not None
        assert row["approval_status"] == "PENDING"


def test_submit_application_already_applied():
    """Test that submission is prevented if student already applied."""
    token = get_student_token()
    res = client.get("/student/elections/1/apply", cookies={COOKIE_NAME: token})
    csrf_token = res.cookies.get("csrf_token")
    if not csrf_token:
        match = re.search(r'name="csrf_token" value="([^"]+)"', res.text)
        csrf_token = match.group(1) if match else None

    with get_db_cursor() as cursor:
        cursor.execute(
            "INSERT INTO candidate_applications (user_id, election_id, manifesto, approval_status) VALUES (1, 1, 'Existing', 'PENDING')"
        )

    data = {"election_id": 1, "manifesto": "New Manifesto", "csrf_token": csrf_token}
    cookies = {COOKIE_NAME: token, "csrf_token": csrf_token}
    response = client.post("/candidates/apply", data=data, cookies=cookies, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/student/candidate-status"


def test_submit_application_wrong_election_status():
    """Test that submission is prevented if election is not UPCOMING."""
    token = get_student_token()
    res = client.get("/student/elections/1/apply", cookies={COOKIE_NAME: token})
    csrf_token = res.cookies.get("csrf_token")
    if not csrf_token:
        match = re.search(r'name="csrf_token" value="([^"]+)"', res.text)
        csrf_token = match.group(1) if match else None

    data = {
        "election_id": 2,  # Active
        "manifesto": "I want to apply to active election",
        "csrf_token": csrf_token,
    }
    cookies = {COOKIE_NAME: token, "csrf_token": csrf_token}
    response = client.post("/candidates/apply", data=data, cookies=cookies, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/student/candidate-status"


def test_submit_application_missing_csrf():
    """Test that submission is prevented without CSRF token."""
    token = get_student_token()
    data = {"election_id": 1, "manifesto": "Manifesto", "csrf_token": "wrong-token"}
    cookies = {COOKIE_NAME: token}
    response = client.post("/candidates/apply", data=data, cookies=cookies)
    assert response.status_code == 403


def test_view_candidate_status_success():
    """Test that students can view their application status."""
    token = get_student_token()
    with get_db_cursor() as cursor:
        cursor.execute(
            "INSERT INTO candidate_applications (user_id, election_id, manifesto, approval_status) VALUES (1, 1, 'Manifesto 1', 'PENDING')"
        )
        cursor.execute(
            "INSERT INTO candidate_applications (user_id, election_id, manifesto, approval_status) VALUES (1, 2, 'Manifesto 2', 'APPROVED')"
        )

    response = client.get("/student/candidate-status", cookies={COOKIE_NAME: token})
    assert response.status_code == 200
    assert "Upcoming Election" in response.text
    assert "Active Election" in response.text
    assert "Pending" in response.text
    assert "Approved" in response.text


def test_view_candidate_status_unauthenticated():
    """Test that unauthenticated users are redirected from status page."""
    response = client.get("/student/candidate-status", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["location"]
