# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🔧 Common Development Commands

### Setup
1. Clone the repository and navigate to the project directory.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables by editing `.env` (see `.env.example` for required variables).
5. Run database migrations:
   ```bash
   alembic upgrade head
   ```
6. Seed the database:
   ```bash
   python database/seed.py
   ```

### Running the Application
Start the development server with hot reload:
```bash
uvicorn app:app --reload
```
The application will be available at `http://localhost:8000`.

### Running Tests
Execute the test suite with pytest:
```bash
pytest
```
Run only unit tests (no database required):
```bash
pytest -m "not integration"
```

### Linting & Type Checking
```bash
ruff check .          # Lint
mypy app.py           # Type check
black .               # Format
```

### Database Migrations
```bash
alembic upgrade head     # Apply all migrations
alembic downgrade -1     # Rollback last migration
alembic revision --autogenerate -m "description"  # Create new migration
```

### Seeding Admin Account
```bash
python database/create_admin.py
```

### Docker
```bash
docker compose up -d          # Start app + DB
docker compose down           # Stop
docker build -t voting-system .  # Build image
```

## 🏗️ Code Architecture & Structure

### Overview
A secure, web-based election management platform built with **FastAPI** (backend), **Jinja2 templates** (frontend), and **MySQL** (database). Uses JWT authentication with role-based access control (STUDENT, ADMIN).

### Key Directories & Files

- `app.py` — Main FastAPI application entrypoint. Route definitions, dependency injection, and app setup.
- `config.py` — Centralized type-safe configuration via `pydantic-settings` (reads from `.env`).
- `middleware.py` — `RequestLoggingMiddleware` (structured JSON logging), `AppErrorHandlerMiddleware`, security headers.
- `exceptions.py` — Custom exception classes (`AuthError`, `ForbiddenError`, `NotFoundError`, `ValidationError`, etc.).
- `database/` — Database utilities and seeding scripts.
  - `connection.py` — MySQL connection pool with `mysql.connector.pooling`, retry logic, context manager.
  - `seed.py` — Seeds admin and student accounts.
  - `create_admin.py` — Interactive admin account creation.
  - `schema.sql` — Full DDL reference for all 6 tables.
- `services/` — Business logic layer (decoupled from routes).
  - `auth_service.py` — JWT creation/decoding, registration, login, password hashing.
  - `election_service.py` — Election CRUD, dashboard stats, results, pagination, vote trends.
  - `candidate_service.py` — Candidate application CRUD, bulk approval/rejection.
  - `vote_service.py` — Voting sessions, vote submission with verification, duplicate prevention.
  - `user_service.py` — User profile operations, department listing.
  - `file_service.py` — File upload validation, S3 storage (production) / local storage (dev).
  - `audit_service.py` — Audit logging for admin actions with pagination and filters.
  - `breach_service.py` — HIBP k-anonymity password breach checking.
  - `cache_service.py` — Redis caching layer (graceful fallback if unavailable).
  - `export_service.py` — CSV and PDF export for election results.
  - `task_service.py` — Background task management via RQ.
- `schemas/` — Pydantic models for request/response validation.
- `alembic/` — Database migration framework. Use `alembic upgrade head` to apply.
- `jobs/` — Background job definitions (e.g., CSV/PDF export via RQ worker).
- `templates/` — Jinja2 HTML templates.
  - `base.html` — Base layout with security meta tags, toast notifications, breadcrumbs.
  - `partials/` — Reusable fragments: navbar, sidebar, breadcrumb, flash messages, form fields, dashboard chart.
  - Admin and student views for elections, candidates, voting, verification, results, profiles.
- `static/` — CSS and JavaScript assets.
- `uploads/` — User-uploaded files (profiles, selfies, signatures). Gitignored.
- `tests/` — Pytest test suite with mock DB cursor fixtures.
- `worker.py` — RQ worker entry point for background job processing.

### Key Technologies
- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: Jinja2 templates with HTML/CSS/JavaScript
- **Database**: MySQL via `mysql-connector-python`, managed with Alembic migrations
- **Authentication**: JWT (PyJWT) with HTTP-only cookies, remember-me support
- **Password Security**: Werkzeug hashing + HIBP breach checking
- **File Storage**: Local (development) or S3 (production)
- **Caching**: Redis (optional, graceful fallback)
- **Background Jobs**: RQ (Redis Queue)
- **Error Tracking**: Sentry (optional, gated by `SENTRY_DSN`)
- **Export**: CSV (stdlib `csv`) and PDF (`reportlab`)
- **Testing**: Pytest with coverage
- **CI/CD**: GitHub Actions (lint → test → build → push to ECR → deploy to EC2)
- **Containerization**: Docker + docker-compose

### Authentication Flow
- Users log in via `/login` or `/admin/login`, which sets an HTTP-only cookie with a JWT token.
- Access tokens are configurable (default 24h, shorter with remember-me).
- Protected routes verify via `get_current_user` dependency.
- Roles checked via `require_role` dependency (admin_guard, student_guard).

### Election Lifecycle
Elections progress through states: `UPCOMING` → `ACTIVE` → `ENDED` based on start/end times.
- Only admins can create, edit, delete, or clone elections.
- Students view and vote in active elections (one vote per election).
- Vote verification requires uploading a selfie or signature per vote.
- Results are hidden until explicitly published by an admin.

### Important Notes
- `.env` must contain database connection details and `JWT_SECRET` (required in production).
- Passwords hashed with `generate_password_hash`, verified with `check_password_hash`.
- In production, uploads go to S3; local storage is used in development.
- Redis is optional — all features degrade gracefully if unavailable.
- RQ worker processes background export jobs; start with `python worker.py`.
- File uploads validated with Pillow (image content verification, not just extension).

## 📝 Contributing Guidelines
1. Follow existing code style — PEP 8, line length 100, double quotes.
2. Write tests for new functionality in `tests/` (pytest with mock DB cursor).
3. Run `ruff check . && mypy app.py` before committing.
4. Update Alembic migrations if schema changes.
5. Keep Jinja2 templates DRY — use partials for reusable components.
6. Ensure new endpoints have proper authentication and authorization checks.
7. Log admin actions via `audit_service.log_action()`.
