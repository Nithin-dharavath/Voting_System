# Spec: Student Election List

## Overview
Authenticated students can browse elections and open an election detail page from their dashboard.

## Depends on
- 02-login
- 04-admin-election

## Routes
- `GET /student/elections` - list elections - logged-in student

## Database changes
No database changes.

## Templates
- Create: `templates/student_elections.html`
- Modify: `templates/student_dashboard.html` to link to the list

## Files to change
- `app.py`
- `templates/student_dashboard.html`

## Files to create
- `templates/student_elections.html`

## New dependencies
No new dependencies

## Rules for implementation
- Use the existing student guard.
- Query elections with parameterized SQL.
- Display title, description, start time, end time, and status.
- Link each election to `/student/elections/{id}` if the detail route exists.
- Use existing CSS variables and layout patterns.

## Definition of done
- Logged-in students can open `/student/elections`.
- Elections render with key metadata.
- Unauthenticated users redirect to `/login`.
- Students cannot access admin routes through this flow.
