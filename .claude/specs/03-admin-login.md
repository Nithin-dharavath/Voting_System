---
# Spec: Admin Login

## Overview
The Admin Login feature provides a dedicated authentication entry point for administrators. While the core authentication mechanism is shared, a separate login flow for admins ensures that they are directed to the admin portal and receive appropriate feedback using the admin-specific login template. This prevents leakage of admin-specific UI patterns into the student login flow and allows for future admin-only security enhancements.

## Depends on
02-login

## Routes
- `GET /admin/login` — Admin login page — public
- `POST /auth/admin-login` — Authenticate admin user and issue JWT — public

## Database changes
No database changes.

## Templates
- **Modify:** `templates/admin-login.html` — Ensure the form posts to `/auth/admin-login`.

## Files to change
- `app.py` — Implement `POST /auth/admin-login` and verify `GET /admin/login`.

## Files to create
No new files.

## New dependencies
No new dependencies.

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
- Ensure that an admin login attempt only succeeds if the user role is `ADMIN`.

## Definition of done
- Navigating to `/admin/login` renders the admin-specific login page.
- Submitting the admin login form sends a request to `/auth/admin-login`.
- An administrator with valid credentials is redirected to `/admin/dashboard`.
- A student attempting to log in via `/auth/admin-login` is rejected with an appropriate error message.
- Invalid credentials for an admin result in an error message on the `admin-login.html` page.
- The admin login flow is distinct from the student login flow (`/auth/login`).
---
