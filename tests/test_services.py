from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import jwt
import pytest
from werkzeug.security import generate_password_hash

from exceptions import AuthError, ValidationError
from services import auth_service
from services.auth_service import configure_jwt, get_jwt_secret
from services.candidate_service import (
    get_pending_count,
    get_student_candidacy_status,
    has_user_applied,
)
from services.election_service import (
    compute_election_status,
    ensure_datetime,
    format_datetime_simple,
    get_active_elections_count,
)
from services.vote_service import get_user_vote_count, has_user_voted

TEST_JWT_SECRET = "test-secret-key"  # noqa: S105


@pytest.fixture(autouse=True)
def _jwt_secret():
    original = auth_service.JWT_SECRET_KEY
    configure_jwt(TEST_JWT_SECRET)
    yield
    configure_jwt(original)


def _make_mock_cursor(fetchone_return):
    mock_cm = MagicMock()
    mock_cursor = MagicMock()
    mock_cm.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = fetchone_return
    return mock_cm


class TestAuthService:
    def test_configure_jwt(self):
        configure_jwt("custom-secret")
        assert get_jwt_secret() == "custom-secret"
        configure_jwt(TEST_JWT_SECRET)

    def test_create_access_token(self):
        token = auth_service.create_access_token({"user_id": 1, "role": "STUDENT"})
        payload = jwt.decode(token, TEST_JWT_SECRET, algorithms=["HS256"])
        assert payload["user_id"] == 1
        assert payload["role"] == "STUDENT"
        assert "exp" in payload

    def test_decode_access_token_valid(self):
        token = auth_service.create_access_token({"user_id": 1})
        result = auth_service.decode_access_token(token)
        assert result is not None
        assert result["user_id"] == 1

    def test_decode_access_token_invalid(self):
        result = auth_service.decode_access_token("invalid-token")
        assert result is None

    def test_generate_csrf_token(self):
        token1 = auth_service.generate_csrf_token()
        token2 = auth_service.generate_csrf_token()
        assert len(token1) > 20
        assert token1 != token2

    @patch("services.auth_service.get_db_cursor")
    def test_register_user_success(self, mock_get_cursor):
        mock_get_cursor.return_value = _make_mock_cursor(None)

        result = auth_service.register_user(
            "Test User", "test@example.com", "password123", "CS", "2024"
        )
        assert result["message"] == "Registration successful! You can now login."

        cursor = mock_get_cursor.return_value.__enter__.return_value
        cursor.execute.assert_any_call(
            "SELECT user_id FROM users WHERE email = %s", ("test@example.com",)
        )

    @patch("services.auth_service.get_db_cursor")
    def test_register_user_duplicate_email(self, mock_get_cursor):
        mock_get_cursor.return_value = _make_mock_cursor({"user_id": 1})

        with pytest.raises(ValidationError, match="Email already registered"):
            auth_service.register_user("Test", "dup@example.com", "password123", "CS", "2024")

    def test_register_user_short_password(self):
        with pytest.raises(ValidationError, match="Password must be at least 8 characters long"):
            auth_service.register_user("Test", "test@example.com", "short", "CS", "2024")

    @patch("services.auth_service.get_db_cursor")
    def test_authenticate_user_success(self, mock_get_cursor):
        mock_get_cursor.return_value = _make_mock_cursor(
            {
                "user_id": 1,
                "email": "user@example.com",
                "password_hash": generate_password_hash("correct_pass"),
                "role": "STUDENT",
            }
        )

        result = auth_service.authenticate_user("user@example.com", "correct_pass")
        assert "token" in result
        assert result["role"] == "STUDENT"

    @patch("services.auth_service.get_db_cursor")
    def test_authenticate_user_invalid_password(self, mock_get_cursor):
        mock_get_cursor.return_value = _make_mock_cursor(
            {
                "user_id": 1,
                "email": "user@example.com",
                "password_hash": generate_password_hash("correct_pass"),
                "role": "STUDENT",
            }
        )

        with pytest.raises(AuthError, match="Invalid email or password"):
            auth_service.authenticate_user("user@example.com", "wrong_pass")

    @patch("services.auth_service.get_db_cursor")
    def test_authenticate_user_nonexistent(self, mock_get_cursor):
        mock_get_cursor.return_value = _make_mock_cursor(None)

        with pytest.raises(AuthError, match="Invalid email or password"):
            auth_service.authenticate_user("nobody@example.com", "pass")

    @patch("services.auth_service.get_db_cursor")
    def test_authenticate_user_require_admin(self, mock_get_cursor):
        mock_get_cursor.return_value = _make_mock_cursor(
            {
                "user_id": 1,
                "email": "user@example.com",
                "password_hash": generate_password_hash("pass"),
                "role": "STUDENT",
            }
        )

        with pytest.raises(AuthError, match="Administrator access required"):
            auth_service.authenticate_user("user@example.com", "pass", require_admin=True)


class TestElectionService:
    def test_compute_election_status_upcoming(self):
        future = datetime.now(UTC) + timedelta(days=1)
        further_future = datetime.now(UTC) + timedelta(days=2)
        assert compute_election_status(future, further_future) == "UPCOMING"

    def test_compute_election_status_active(self):
        past = datetime.now(UTC) - timedelta(hours=1)
        future = datetime.now(UTC) + timedelta(hours=1)
        assert compute_election_status(past, future) == "ACTIVE"

    def test_compute_election_status_ended(self):
        past = datetime.now(UTC) - timedelta(days=2)
        recent_past = datetime.now(UTC) - timedelta(hours=1)
        assert compute_election_status(past, recent_past) == "ENDED"

    def test_ensure_datetime_naive(self):
        dt = datetime(2024, 1, 1, 12, 0, 0)
        result = ensure_datetime(dt)
        assert result.tzinfo is not None
        assert result.tzinfo == UTC

    def test_ensure_datetime_aware(self):
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        result = ensure_datetime(dt)
        assert result == dt

    def test_ensure_datetime_str(self):
        result = ensure_datetime("2024-01-01 12:00:00")
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1

    def test_ensure_datetime_none(self):
        assert ensure_datetime(None) is None

    def test_format_datetime_simple(self):
        dt = datetime(2024, 1, 15, 9, 30, 0, tzinfo=UTC)
        result = format_datetime_simple(dt)
        assert result == "2024-01-15 09:30"

    @patch("services.election_service.get_db_cursor")
    def test_get_active_elections_count(self, mock_get_cursor):
        mock_get_cursor.return_value = _make_mock_cursor({"count": 3})
        assert get_active_elections_count() == 3


class TestCandidateService:
    @patch("services.candidate_service.get_db_cursor")
    def test_has_user_applied_true(self, mock_get_cursor):
        mock_get_cursor.return_value = _make_mock_cursor({"id": 5})
        assert has_user_applied(1, 2) is True

    @patch("services.candidate_service.get_db_cursor")
    def test_has_user_applied_false(self, mock_get_cursor):
        mock_get_cursor.return_value = _make_mock_cursor(None)
        assert has_user_applied(1, 2) is False

    @patch("services.candidate_service.get_db_cursor")
    def test_get_pending_count(self, mock_get_cursor):
        mock_get_cursor.return_value = _make_mock_cursor({"count": 7})
        assert get_pending_count() == 7

    @patch("services.candidate_service.get_db_cursor")
    def test_get_student_candidacy_status_approved(self, mock_get_cursor):
        mock_get_cursor.return_value = _make_mock_cursor({"approval_status": "APPROVED"})
        assert get_student_candidacy_status(1) == "APPROVED"

    @patch("services.candidate_service.get_db_cursor")
    def test_get_student_candidacy_status_none(self, mock_get_cursor):
        mock_get_cursor.return_value = _make_mock_cursor(None)
        assert get_student_candidacy_status(1) is None


class TestVoteService:
    @patch("services.vote_service.get_db_cursor")
    def test_has_user_voted_true(self, mock_get_cursor):
        mock_get_cursor.return_value = _make_mock_cursor({"1": 1})
        assert has_user_voted(1, 2) is True

    @patch("services.vote_service.get_db_cursor")
    def test_has_user_voted_false(self, mock_get_cursor):
        mock_get_cursor.return_value = _make_mock_cursor(None)
        assert has_user_voted(1, 2) is False

    @patch("services.vote_service.get_db_cursor")
    def test_get_user_vote_count(self, mock_get_cursor):
        mock_get_cursor.return_value = _make_mock_cursor({"count": 2})
        assert get_user_vote_count(1) == 2


class TestExceptions:
    def test_auth_error(self):
        err = AuthError()
        assert err.status_code == 401
        assert str(err) == "Authentication failed"

    def test_auth_error_custom(self):
        err = AuthError("Custom message", 403)
        assert err.status_code == 403
        assert str(err) == "Custom message"

    def test_validation_error(self):
        err = ValidationError("Invalid input")
        assert err.status_code == 422

    def test_error_inheritance(self):
        from exceptions import AppError

        assert issubclass(AuthError, AppError)
        assert issubclass(ValidationError, AppError)
