# Spec: Registration

## Overview
Students create accounts with institutional details so the system can authenticate them and enforce one identity per voter.

## Depends on
None

## Routes
- `GET /register` - render the registration page - public
- `POST /auth/register` - create a student account - public

## Database changes
No database changes. Use `users`: `full_name`, `email`, `password_hash`, `department`, `academic_year`, `role`, `is_active`, `created_at`.

## Templates
- Create: `templates/register.html`
- Modify: `templates/base.html` only if needed for navigation

## Files to change
- `app.py`

## Files to create
- `templates/register.html`

## New dependencies
- `python-multipart` if form parsing is not already installed

## Rules for implementation
- No SQLAlchemy or ORMs.
- Use `get_db_cursor()` and parameterized SQL.
- Hash passwords with `werkzeug.security.generate_password_hash`.
- Default role to `STUDENT`.
- Use CSS variables from `static/css/style.css`.
- All templates extend `base.html`.
- Do not hardcode secrets, credentials, upload paths, or server URLs.
- Keep changes minimal and aligned with the current app.

## Definition of done
- `/register` renders a usable form.
- Required fields are validated: `full_name`, `email`, `password`, `department`, `academic_year`.
- Successful registration stores a user with a hashed password.
- Duplicate email registration shows a clear error.
- Template extends `base.html` and follows existing styling.
