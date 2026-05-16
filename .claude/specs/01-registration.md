---
# Spec: Registration

## Overview
Registration is the entry point for students to join the Online Voting System. It allows them to create a secure account using their institutional details, enabling them to later log in and participate in elections. This feature ensures that only eligible students are registered and establishes the unique identity required to enforce the "one student, one vote" rule.

## Depends on
None

## Routes
- `GET /register` — Serve registration page — public
- `POST /auth/register` — Process registration request and create user account — public

## Database changes
No database changes. Uses existing `users` table:
- Fields: `full_name`, `email` (unique), `password_hash`, `department`, `academic_year`, `role` (default: STUDENT), `is_active` (default: true), `created_at`.

## Templates
- **Create:** `templates/register.html`
- **Modify:** `templates/base.html` (Ensure it exists as the base for all pages)

## Files to change
- `app.py`

## Files to create
- `templates/register.html`

## New dependencies
- `python-multipart` (required for FastAPI to handle form data)

## Rules for implementation
- No SQLAlchemy or ORMs.
- Parameterised queries only.
- Passwords hashed with `werkzeug`.
- Use CSS variables, never hardcode hex values.
- All templates extend `base.html`.
- Do not hardcode database passwords, JWT secrets, upload paths, server URLs, or admin credentials.
- Validate uploaded files, rename them safely, and store only file paths.
- Keep changes minimal and aligned with the existing app structure.
- Do not introduce new architecture unless the spec explicitly requires it.

## Definition of done
- Navigating to `/register` renders a functional registration form.
- Validating that the registration form correctly captures and sends `full_name`, `email`, `password`, `department`, and `academic_year`.
- Verifying that a successful registration creates a record in the `users` table with a hashed password using `werkzeug`.
- Confirming that duplicate email registrations are blocked with an appropriate error message.
- Verifying that the registration page extends `base.html` and adheres to the project's CSS conventions.
- Ensuring that the `POST /auth/register` endpoint validates all required fields before attempting database insertion.
---
