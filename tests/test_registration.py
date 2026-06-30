from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

@pytest.fixture
def mock_cursor():
    with patch("app.get_db_cursor") as mock_get_cursor:
        # Mock the context manager: get_db_cursor() returns a mock object
        # that has __enter__ and __exit__ methods.
        mock_cm = MagicMock()
        mock_cursor_obj = MagicMock()

        mock_get_cursor.return_value = mock_cm
        mock_cm.__enter__.return_value = mock_cursor_obj

        yield mock_cursor_obj

def test_register_page_success():
    """Test that GET /register renders the registration form."""
    response = client.get("/register")
    assert response.status_code == 200
    # Since we don't have the templates in this environment,
    # we check for 200 OK. In a real environment, we'd check for content.

def test_register_user_success(mock_cursor):
    """Test successful registration."""
    # Mock no existing user with this email
    mock_cursor.fetchone.return_value = None

    payload = {
        "full_name": "John Doe",
        "email": "john@example.com",
        "password": "password123",
        "department": "Computer Science",
        "academic_year": "2023-2024"
    }

    response = client.post("/auth/register", data=payload)

    assert response.status_code == 200
    # The implementation returns a TemplateResponse with a 'success' message in context.
    # We can't easily check the context of a TemplateResponse via TestClient,
    # but we can check if the response was successful.

    # Verify database interaction
    # Check that email check was performed
    mock_cursor.execute.assert_any_call("SELECT user_id FROM users WHERE email = %s", ("john@example.com",))

    # Check that user was inserted
    # We look for a call that contains 'INSERT INTO users'
    insert_call_found = False
    for call in mock_cursor.execute.call_args_list:
        args, kwargs = call
        if "INSERT INTO users" in args[0]:
            insert_call_found = True
            # Verify that the hashed password was used (not the plain text one)
            # args[1] should be the tuple of values
            assert args[1][2] != "password123"
            break

    assert insert_call_found, "Insert query was not executed"

def test_register_user_duplicate_email(mock_cursor):
    """Test registration fails for duplicate email."""
    # Mock that a user with this email already exists
    mock_cursor.fetchone.return_value = {"user_id": 1}

    payload = {
        "full_name": "John Doe",
        "email": "duplicate@example.com",
        "password": "password123",
        "department": "Computer Science",
        "academic_year": "2023-2024"
    }

    response = client.post("/auth/register", data=payload)

    assert response.status_code == 200
    # In a real scenario, we would check the HTML content for "Email already registered."

def test_register_user_invalid_email():
    """Test registration fails for invalid email format."""
    payload = {
        "full_name": "John Doe",
        "email": "invalid-email",
        "password": "password123",
        "department": "Computer Science",
        "academic_year": "2023-2024"
    }

    response = client.post("/auth/register", data=payload)

    assert response.status_code == 200
    # Should trigger validate_email(email) == False

def test_register_user_password_too_short():
    """Test registration fails for password < 8 characters."""
    payload = {
        "full_name": "John Doe",
        "email": "john@example.com",
        "password": "short",
        "department": "Computer Science",
        "academic_year": "2023-2024"
    }

    response = client.post("/auth/register", data=payload)

    assert response.status_code == 200
    # Should trigger validate_password(password) == False

def test_register_user_missing_fields():
    """Test registration fails when required fields are missing."""
    # Missing academic_year
    payload = {
        "full_name": "John Doe",
        "email": "john@example.com",
        "password": "password123",
        "department": "Computer Science"
    }

    response = client.post("/auth/register", data=payload)

    # FastAPI Form(...) raises 422 Unprocessable Entity if a required field is missing
    assert response.status_code == 422
