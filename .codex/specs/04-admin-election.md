# Spec: Admin Election

## Overview
Admins can create, list, update, and delete elections. This establishes the election lifecycle students and candidates depend on.

## Depends on
03-admin-login

## Routes
- `GET /admin/elections` - list elections - admin
- `GET /admin/elections/create` - render create form - admin
- `POST /admin/elections` - create election - admin
- `GET /admin/elections/{id}` - render edit/detail page - admin
- `POST /admin/elections/{id}/update` - update election - admin
- `POST /admin/elections/{id}/delete` - delete election - admin

## Database changes
No database changes. Use `elections`: `id`, `title`, `description`, `start_time`, `end_time`, `result_published`, `created_by`, `created_at`.

## Templates
- Create: `templates/admin_elections.html`
- Create: `templates/admin_election_create.html`
- Create: `templates/admin_election_edit.html`

## Files to change
- `app.py`

## Files to create
- `templates/admin_elections.html`
- `templates/admin_election_create.html`
- `templates/admin_election_edit.html`

## New dependencies
No new dependencies

## Rules for implementation
- Protect every route with admin role verification.
- Validate required fields and enforce `start_time < end_time`.
- Use parameterized SQL.
- Use existing dashboard/navigation patterns.
- Keep delete behavior explicit and redirect back to the list.

## Definition of done
- Admins can list, create, edit, and delete elections.
- Created elections appear in `/admin/elections`.
- Invalid schedules are rejected with a visible error.
- Students and unauthenticated users cannot access admin election routes.
- Times are stored and displayed consistently.
