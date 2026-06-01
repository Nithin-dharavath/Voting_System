# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Run the FastAPI server with auto-reload
uvicorn app:app --reload
```

### Testing
```bash
# Run all tests using pytest
pytest

# Run a specific test file
pytest tests/test_auth.py

# Run a specific test case
pytest tests/test_auth.py::test_function_name
```

### Database Management
```bash
# Seed the database with initial data
python database/seed.py

# Create a default administrator account
python database/create_admin.py
```

## High-Level Architecture

The system is a modular monolithic REST application using **FastAPI** and **MySQL**.

- **Frontend**: Server-side rendered templates using **Jinja2** with vanilla HTML/CSS/JS.
- **Backend**: FastAPI handles routing, authentication (JWT in cookies), and business logic.
- **Database**: Direct MySQL interaction via `get_db_cursor()` (No ORM).
- **Auth Flow**:
    - `AuthMiddleware` intercepts requests to decode JWTs from cookies.
    - `admin_guard` and `student_guard` dependencies enforce Role-Based Access Control (RBAC).
- **Voting Workflow**:
    - Student $\rightarrow$ Session $\rightarrow$ Vote $\rightarrow$ Verification $\rightarrow$ Commit.
    - Uses ACID transactions for vote submission to ensure atomicity.

## Project Constraints & Guardrails

### Implementation Rules
- **Database**: Strictly **no SQLAlchemy or ORMs**. Use parameterized queries only via `get_db_cursor()`.
- **Security**: 
    - Passwords must be hashed with `werkzeug.security`.
    - Session tokens must be stored in `HttpOnly`, `SameSite=Lax` cookies.
    - All POST routes must be protected by CSRF validation.
- **Frontend**:
    - All templates must extend `base.html`.
    - Use CSS variables for colors; never hardcode hex values.
- **Configuration**: Never hardcode secrets (DB passwords, JWT secrets, upload paths). Use `.env` or environment variables.
- **Uploads**: Validate file types, rename files safely, and store only the `file_path` in the database.

### Core Domain Rules
- **Voting**:
    - Election must be `ACTIVE`.
    - Only one vote per student per election.
    - Candidates must be `APPROVED` to receive votes.
    - Verification must exist before the final vote is committed.
    - No new sessions if the election has $< 2$ minutes remaining.
- **Results**:
    - Results are hidden (`result_published = false`) until the admin explicitly publishes them.
    - Students cannot see live counts.

## Key Entities & Naming

### Required Field Names
Maintain consistency with these fields:
- `student_id`, `election_id`, `candidate_application_id`, `approval_status`, `result_published`, `verification_type`, `file_path`, `created_at`.

### Required Values
- **Roles**: `STUDENT`, `ADMIN`
- **Election Status**: `UPCOMING`, `ACTIVE`, `ENDED`
- **Candidate Status**: `PENDING`, `APPROVED`, `REJECTED`
- **Verification Types**: `SELFIE`, `SIGNATURE`
