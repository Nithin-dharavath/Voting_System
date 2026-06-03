# Spec: Admin Login

## Overview
Administrators get a dedicated login flow that reuses authentication mechanics but only accepts users with role `ADMIN`.

## Depends on
02-login

## Routes
- `GET /admin/login` - admin login page - public
- `POST /auth/admin-login` - authenticate admin user - public

## Database changes
No database changes.

## Templates
- Modify: `templates/admin-login.html` so the form posts to `/auth/admin-login`

## Files to change
- `app.py`

## Files to create
No new files

## New dependencies
No new dependencies

## Rules for implementation
- Only users with role `ADMIN` can succeed.
- Verify passwords with `werkzeug.security.check_password_hash`.
- Use the existing signed-cookie/JWT mechanism.
- Parameterize all SQL.
- Keep student login behavior unchanged.

## Definition of done
- `/admin/login` renders the admin login page.
- Valid admin credentials redirect to `/admin/dashboard`.
- Student credentials are rejected on `/auth/admin-login`.
- Invalid admin credentials show an error on `admin-login.html`.
- The admin flow remains distinct from `/auth/login`.
