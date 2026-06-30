from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_register_page_success():
    response = client.get("/register")
    assert response.status_code == 200


def test_register_user_success(mock_cursor):
    mock_cursor.fetchone.return_value = None
    payload = {
        "full_name": "John Doe",
        "email": "john@example.com",
        "password": "password123",
        "department": "Computer Science",
        "academic_year": "2023-2024",
    }
    response = client.post("/auth/register", data=payload)
    assert response.status_code == 200
    mock_cursor.execute.assert_any_call(
        "SELECT user_id FROM users WHERE email = %s", ("john@example.com",)
    )
    insert_call_found = False
    for call in mock_cursor.execute.call_args_list:
        args, kwargs = call
        if "INSERT INTO users" in args[0]:
            insert_call_found = True
            assert args[1][2] != "password123"
            break
    assert insert_call_found, "Insert query was not executed"


def test_register_user_duplicate_email(mock_cursor):
    mock_cursor.fetchone.return_value = {"user_id": 1}
    payload = {
        "full_name": "John Doe",
        "email": "duplicate@example.com",
        "password": "password123",
        "department": "Computer Science",
        "academic_year": "2023-2024",
    }
    response = client.post("/auth/register", data=payload)
    assert response.status_code == 200


def test_register_user_password_too_short():
    payload = {
        "full_name": "John Doe",
        "email": "john@example.com",
        "password": "short",
        "department": "Computer Science",
        "academic_year": "2023-2024",
    }
    response = client.post("/auth/register", data=payload)
    assert response.status_code == 200


def test_register_user_missing_fields():
    payload = {
        "full_name": "John Doe",
        "email": "john@example.com",
        "password": "password123",
        "department": "Computer Science",
    }
    response = client.post("/auth/register", data=payload)
    assert response.status_code == 422
