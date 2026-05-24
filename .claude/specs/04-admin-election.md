---
# Spec: Admin Election

## Overview
The Admin Election feature allows administrators to manage the lifecycle of elections within the system. This includes creating new elections, defining their titles, descriptions, and schedules (start and end times), and managing existing elections through updates or deletions. This is a foundational step that enables students to later view and participate in elections.

## Depends on
03-admin-login

## Routes
- `GET /admin/elections` — List all elections — admin
- `GET /admin/elections/create` — Election creation form — admin
- `POST /admin/elections` — Process election creation — admin
- `GET /admin/elections/:id` — View and edit election details — admin
- `POST /admin/elections/:id/update` — Process election update — admin
- `POST /admin/elections/:id/delete` — Delete an election — admin

## Database changes
No database changes. Uses existing `elections` table:
- Fields: `id`, `title`, `description`, `start_time`, `end_time`, `result_published` (default: false), `created_by`, `created_at`.

## Templates
- **Create:** `templates/admin_elections.html` — List of all elections.
- **Create:** `templates/admin_election_create.html` — Form to create a new election.
- **Create:** `templates/admin_election_edit.html` — Form to edit an existing election.

## Files to change
- `app.py` — Implement all election management routes.

## Files to create
- `templates/admin_elections.html`
- `templates/admin_election_create.html`
- `templates/admin_election_edit.html`

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
- Ensure all routes are protected by admin role verification.
- Use `datetime` for handling `start_time` and `end_time`.

## Definition of done
- Admin can access `/admin/elections` and see a list of all elections.
- Admin can navigate to `/admin/elections/create` and successfully create a new election.
- Successfully created elections appear in the elections list.
- Admin can navigate to `/admin/elections/:id` and modify the election details.
- Admin can delete an election, and it is removed from the list.
- Attempting to access any of these routes as a student or unauthenticated user redirects to `/admin/login`.
- Election schedules (start/end times) are correctly stored and displayed in the database and UI.
---
