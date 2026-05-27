---
# Spec: Student Election List

## Overview
This feature allows authenticated students to view a list of all available elections. It provides the primary entry point for students to discover active elections they can vote in and upcoming elections.

## Depends on
- 04-admin-election
- 02-login

## Routes
- `GET /student/elections` — List all elections — logged-in student

## Database changes
No database changes.

## Templates
- **Create:** `templates/student_elections.html`
- **Modify:** `templates/student_dashboard.html` (add link to elections list)

## Files to change
- `app.py`

## Files to create
- `templates/student_elections.html`

## New dependencies
No new dependencies.

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
- Student can navigate to `/student/elections` after logging in.
- The page displays a list of elections (title, description, start/end times).
- Each election item links to its detail page `/student/elections/{id}`.
- Unauthenticated users are redirected to `/login`.
- Students are redirected back if they try to access admin routes.
---
