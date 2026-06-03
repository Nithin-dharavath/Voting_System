# Repository Guidelines

## Project Structure & Module Organization

This is a FastAPI-based online voting system with server-rendered Jinja templates and direct MySQL access. The main application entrypoint is `app.py`. Database utilities and setup scripts live in `database/`, including `connection.py`, `seed.py`, and `create_admin.py`. UI templates are in `templates/`, reusable template fragments are in `templates/partials/`, and frontend assets are in `static/css/` and `static/js/`. Tests are in `tests/` and project notes are in `docs/` and `workflow/`. Do not edit generated folders such as `venv/`, `__pycache__/`, `.pytest_cache/`, or uploaded files in `uploads/`.

## Build, Test, and Development Commands

- `python -m venv venv`: create a local virtual environment.
- `venv\Scripts\activate`: activate the virtual environment on Windows PowerShell.
- `pip install -r requirements.txt`: install FastAPI, pytest, MySQL, and template dependencies.
- `uvicorn app:app --reload`: run the local development server with auto-reload.
- `pytest`: run the full test suite.
- `pytest tests/test_auth.py`: run one test file.
- `python database/seed.py`: seed initial data.
- `python database/create_admin.py`: create a default admin account.

## Coding Style & Naming Conventions

Use Python 4-space indentation and keep route handlers, validation, database operations, and error handling clear and explicit. Use `snake_case` for functions, variables, and test names. Templates should extend `base.html`; shared admin navigation belongs in `templates/partials/`. Use CSS variables from `static/css/style.css` instead of hardcoded colors. Keep domain values consistent: roles are `STUDENT` and `ADMIN`; election statuses are `UPCOMING`, `ACTIVE`, and `ENDED`; candidate statuses are `PENDING`, `APPROVED`, and `REJECTED`.

## Testing Guidelines

Tests use `pytest` and FastAPI `TestClient`. Name files `test_*.py` and functions `test_<behavior>()`. Add or update tests for changed routes, auth rules, database behavior, and important template-visible outcomes. Prefer focused tests that create their own test data when possible.

## Security & Configuration Tips

Use `get_db_cursor()` from `database.connection`; do not add an ORM. Always use parameterized SQL. Keep secrets, database credentials, JWT secrets, and upload paths in `.env` or environment variables. Passwords must be hashed with `werkzeug.security`. Session cookies should remain `HttpOnly` and `SameSite=Lax`. Validate upload types and store only file paths in the database.

## Commit & Pull Request Guidelines

Recent commits use short, lowercase, feature-oriented messages such as `user profile page` and `filter category`; keep messages concise and specific. Pull requests should include a summary, test results, linked issue or workflow phase when relevant, and screenshots for visible UI changes.
