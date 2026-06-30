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
4. Configure environment variables by editing `.env` (see `.env.example` or README for required variables).
5. Seed the database:
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

### Seeding Admin Account (if needed)
```bash
python database/create_admin.py
```

## 🏗️ Code Architecture & Structure

### Overview
This is a web-based election management platform built with **FastAPI** (backend), **Jinja2 templates** (frontend), and **MySQL** (database). It uses JWT for authentication and features role-based access control (STUDENT, ADMIN).

### Key Directories & Files

- `app.py` - Main FastAPI application entrypoint. Contains route definitions, middleware, and application setup.
- `templates/` - Jinja2 HTML templates for server-side rendered views.
  - `base.html` - Base layout template.
  - `partials/` - Reusable template fragments (e.g., navigation, forms).
- `static/` - Static assets (CSS, JavaScript, images).
  - `css/` - Stylesheets.
  - `js/` - Client-side JavaScript.
- `database/` - Database utilities and seeding scripts.
  - `connection.py` - MySQL connection utility using `mysql-connector-python`.
  - `seed.py` - Populates the database with initial data (admin and student accounts).
  - `create_admin.py` - Creates an administrator account.
- `uploads/` - Directory for user-uploaded files (profile pictures, vote verification evidence).
- `tests/` - Pytest test suite for backend functionality.
- `docs/` - Additional documentation (architecture, API details, etc.).
- `workflow/` - Development phase notes (historical, may be outdated).

### Key Technologies
- **Backend**: FastAPI (Python 3.10+)
- **Frontend**: Jinja2 templates with HTML/CSS/JavaScript
- **Database**: MySQL via `mysql-connector-python`
- **Authentication**: JWT (PyJWT) with access tokens stored in HTTP-only cookies
- **Password Hashing**: Werkzeug security utilities
- **File Uploads**: Local storage in `uploads/` directory
- **Testing**: Pytest

### Authentication Flow
- Users log in via `/login` endpoint, which sets an HTTP-only cookie containing a JWT token.
- Protected routes verify the token via a dependency (`get_current_user` in `app.py`).
- Roles are checked via dependencies (`require_role` dependency).

### Election Lifecycle
Elections progress through states: `UPCOMING` → `ACTIVE` → `ENDED` based on start/end times.
- Only admins can create/modify elections.
- Students can view and vote in active elections.
- Vote verification requires uploading a selfie/signature per vote.
- Results are hidden until published by an admin.

### Important Notes
- The `.env` file must contain MySQL connection details (see README for required variables).
- Passwords are hashed using `generate_password_hash` and verified with `check_password_hash`.
- File uploads are stored in the `uploads/` directory; ensure this directory exists and is writable.
- The seed script creates an admin account and several student accounts for testing (see README for credentials).

## 📝 Contributing Guidelines
When contributing to this codebase:
1. Follow the existing code style (PEP 8 for Python, consistent with surrounding code).
2. Write tests for new functionality in the `tests/` directory.
3. Update the database seed scripts if schema changes require new seed data.
4. Keep Jinja2 templates DRY by using partials for reusable components.
5. Ensure any new endpoints have proper authentication and authorization checks.
