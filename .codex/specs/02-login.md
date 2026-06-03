# Spec: Login

## Overview
Students and admins authenticate with email and password. A signed cookie-backed session/JWT allows access to protected dashboards.

## Depends on
01-registration

## Routes
- `GET /login` - student login page - public
- `GET /admin/login` - admin login page - public
- `POST /auth/login` - authenticate student user - public

## Database changes
No database changes.

## Templates
- Modify: `templates/base.html` for auth-aware navigation if not already present

## Files to change
- `app.py`

## Files to create
No new files

## New dependencies
- `PyJWT` if token signing is not already installed

## Rules for implementation
- Verify passwords with `werkzeug.security.check_password_hash`.
- Use `JWT_SECRET` from environment/config.
- Store the token in an HttpOnly, SameSite=Lax cookie.
- Keep student and admin redirect behavior explicit.
- Parameterize all SQL.
- Do not hardcode secrets or admin credentials.

## Definition of done
- Student login redirects to `/student/dashboard`.
- Admin login redirects to `/admin/dashboard` or the dedicated admin-login flow if implemented in step 03.
- Invalid credentials render a clear login error.
- Logged-in users see Dashboard and Logout navigation.
- Logged-out users see Login and Register navigation.
- Protected routes redirect unauthenticated users to the correct login page.
