from unittest.mock import MagicMock, patch

import pytest

SERVICE_MODULES = [
    "services.auth_service",
    "services.election_service",
    "services.candidate_service",
    "services.vote_service",
    "services.user_service",
]


@pytest.fixture(autouse=True)
def _disable_breach_check():
    from config import settings

    original = settings.breach_check_enabled
    settings.breach_check_enabled = False
    yield
    settings.breach_check_enabled = original


@pytest.fixture
def mock_cursor():
    """Patches get_db_cursor in app + all service modules + database.connection.
    Yields the cursor mock so tests can configure fetchone/fetchall return values.
    """
    mock_cm = MagicMock()
    mock_cursor_obj = MagicMock()
    mock_cm.__enter__.return_value = mock_cursor_obj

    patchers = [
        patch("database.connection.get_db_cursor", return_value=mock_cm),
        patch("app.get_db_cursor", return_value=mock_cm),
    ] + [patch(f"{mod}.get_db_cursor", return_value=mock_cm) for mod in SERVICE_MODULES]

    for p in patchers:
        p.start()

    yield mock_cursor_obj

    for p in patchers:
        p.stop()
