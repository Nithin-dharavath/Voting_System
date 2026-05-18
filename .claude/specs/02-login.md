---
# Spec: Login

## Overview
The Login feature enables registered users (STUDENT and ADMIN) to authenticate themselves using their email and password. Upon successful authentication, a JWT (JSON Web Token) is issued to maintain the session, allowing users to access protected routes like the dashboard.

## Depends on
01-registration

## Routes
- `GET /login` — Student login page — public
- `GET /admin/login` — Admin login page — public
- `POST /auth/login` — Authenticate user and issue JWT — public

## Database changes
No database changes. Uses existing `users` table.

## Templates
- **Modify**: `templates/base.html` — Add dynamic navigation links (Login/Logout) based on authentication status.

## Files to change
- `app.py` — Implement `POST /auth/login` and authentication middleware/dependency.

## Files to create
No new files.

## New dependencies
- `PyJWT`

## Rules for implementation
- No SQLAlchemy or ORMs.
- Parameterised queries only.
- Passwords verified using `werkzeug.security.check_password_hash`.
- Use CSS variables, never hardcode hex values.
- All templates extend `base.html`.
- Do not hardcode database passwords, JWT secrets, upload paths, server URLs, or admin credentials.
- Validate uploaded files, rename them safely, and store only file paths.
- Keep changes minimal and aligned with the existing app structure.
- Do not introduce new architecture unless the spec explicitly requires it.
- Use a secure `JWT_SECRET` from environment variables.
- Store JWT in an HTTP-only cookie for security.

## Definition of done
- A student can log in with valid credentials and be redirected to `/student/dashboard`.
- An admin can log in with valid credentials and be redirected to `/admin/dashboard`.
- Invalid credentials result in an error message on the login page.
- Logged-in users see "Logout" and "Dashboard" links in the navigation bar.
- Logged-out users see "Login" and "Register" links in the navigation bar.
- Attempting to access a protected route without a valid JWT redirects to the login page.
---
