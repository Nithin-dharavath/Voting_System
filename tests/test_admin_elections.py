import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app import app, COOKIE_NAME, create_access_token

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
def admin_client(client):
    """Client authenticated as an administrator."""
    token = create_access_token({"user_id": 1, "role": "ADMIN", "email": "admin@example.com"})
    client.cookies.set(COOKIE_NAME, token)
    return client

@pytest.fixture
def student_client(client):
    """Client authenticated as a student."""
    token = create_access_token({"user_id": 2, "role": "STUDENT", "email": "student@example.com"})
    client.cookies.set(COOKIE_NAME, token)
    return client

# --- Auth Guard Tests ---

def test_list_elections_unauthenticated(client):
    response = client.get("/admin/elections", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/login"

def test_list_elections_student(student_client):
    response = student_client.get("/admin/elections", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/login"

def test_create_election_page_unauthenticated(client):
    response = client.get("/admin/elections/create", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/login"

def test_create_election_page_student(student_client):
    response = student_client.get("/admin/elections/create", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/login"

def test_edit_election_page_unauthenticated(client):
    response = client.get("/admin/elections/1", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/login"

def test_edit_election_page_student(student_client):
    response = student_client.get("/admin/elections/1", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/login"

def test_create_election_post_unauthenticated(client):
    response = client.post("/admin/elections", data={"title": "Test"}, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/login"

def test_create_election_post_student(student_client):
    response = student_client.post("/admin/elections", data={"title": "Test"}, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/login"

def test_update_election_post_unauthenticated(client):
    response = client.post("/admin/elections/1/update", data={"title": "Test"}, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/login"

def test_update_election_post_student(student_client):
    response = student_client.post("/admin/elections/1/update", data={"title": "Test"}, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/login"

def test_delete_election_post_unauthenticated(client):
    response = client.post("/admin/elections/1/delete", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/login"

def test_delete_election_post_student(student_client):
    response = student_client.post("/admin/elections/1/delete", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/login"

# --- Feature Tests ---

def test_list_elections_admin(admin_client, mock_cursor):
    # Mock return value for elections
    mock_cursor.fetchall.return_value = [
        {"id": 1, "title": "Election 1", "description": "Desc 1", "start_time": "2026-06-01", "end_time": "2026-06-02", "result_published": 0},
        {"id": 2, "title": "Election 2", "description": "Desc 2", "start_time": "2026-06-03", "end_time": "2026-06-04", "result_published": 0},
    ]

    response = admin_client.get("/admin/elections")
    assert response.status_code == 200
    assert "Election 1" in response.text
    assert "Election 2" in response.text
    mock_cursor.execute.assert_called_with("SELECT id, title, description, start_time, end_time, status, result_published FROM elections ORDER BY created_at DESC")

def test_create_election_page_admin(admin_client):
    response = admin_client.get("/admin/elections/create")
    assert response.status_code == 200
    assert "admin_election_create.html" in response.text or "Create Election" in response.text

def test_create_election_success(admin_client, mock_cursor):
    payload = {
        "title": "New Election",
        "description": "Test Description",
        "start_time": "2026-06-01T09:00",
        "end_time": "2026-06-01T17:00"
    }
    response = admin_client.post("/admin/elections", data=payload, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/elections?success=created"

    # Check if DB call was made with correct data
    args, _ = mock_cursor.execute.call_args
    assert args[0] == "INSERT INTO elections (title, description, start_time, end_time, created_by) VALUES (%s, %s, %s, %s, %s)"
    assert args[1][0] == "New Election"
    assert args[1][1] == "Test Description"
    # start_time and end_time should be converted to datetime objects in the app, so we verify they are not strings
    assert hasattr(args[1][2], 'year')
    assert hasattr(args[1][3], 'year')
    assert args[1][4] == 1 # user_id from admin_client fixture

def test_create_election_invalid_dates(admin_client, mock_cursor):
    # End time before start time
    payload = {
        "title": "Invalid Election",
        "description": "Test",
        "start_time": "2026-06-02T09:00",
        "end_time": "2026-06-01T09:00"
    }
    response = admin_client.post("/admin/elections", data=payload)

    assert response.status_code == 200
    assert "End time must be after start time" in response.text
    mock_cursor.execute.assert_not_called()

def test_create_election_bad_format(admin_client, mock_cursor):
    payload = {
        "title": "Bad Format",
        "description": "Test",
        "start_time": "not-a-date",
        "end_time": "not-a-date"
    }
    response = admin_client.post("/admin/elections", data=payload)

    assert response.status_code == 200
    assert "An error occurred" in response.text
    mock_cursor.execute.assert_not_called()

def test_edit_election_page_admin(admin_client, mock_cursor):
    mock_cursor.fetchone.return_value = {
        "id": 1, "title": "Existing Election", "description": "Existing Desc",
        "start_time": "2026-06-01", "end_time": "2026-06-02", "result_published": 0
    }

    response = admin_client.get("/admin/elections/1")
    assert response.status_code == 200
    assert "Existing Election" in response.text
    mock_cursor.execute.assert_called_with("SELECT id, title, description, start_time, end_time, result_published FROM elections WHERE id = %s", (1,))

def test_edit_election_page_not_found(admin_client, mock_cursor):
    mock_cursor.fetchone.return_value = None

    response = admin_client.get("/admin/elections/999", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/elections"

def test_update_election_success(admin_client, mock_cursor):
    payload = {
        "title": "Updated Title",
        "description": "Updated Description",
        "start_time": "2026-06-01T10:00",
        "end_time": "2026-06-01T18:00"
    }
    response = admin_client.post("/admin/elections/1/update", data=payload, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/elections?success=updated"

    args, _ = mock_cursor.execute.call_args
    assert args[0] == "UPDATE elections SET title = %s, description = %s, start_time = %s, end_time = %s WHERE id = %s"
    assert args[1][0] == "Updated Title"
    assert args[1][1] == "Updated Description"
    assert args[1][4] == 1 # election id

def test_update_election_invalid_dates(admin_client, mock_cursor):
    payload = {
        "title": "Invalid Update",
        "description": "Test",
        "start_time": "2026-06-02T09:00",
        "end_time": "2026-06-01T09:00"
    }
    # Need mock_cursor.fetchone for the error page to load the election details back
    mock_cursor.fetchone.return_value = {
        "id": 1, "title": "Existing", "description": "Desc",
        "start_time": "2026-06-01", "end_time": "2026-06-02", "result_published": 0
    }
    response = admin_client.post("/admin/elections/1/update", data=payload)

    assert response.status_code == 200
    assert "End time must be after start time" in response.text

def test_delete_election_success(admin_client, mock_cursor):
    response = admin_client.post("/admin/elections/1/delete", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/elections?success=deleted"
    mock_cursor.execute.assert_called_with("DELETE FROM elections WHERE id = %s", (1,))
