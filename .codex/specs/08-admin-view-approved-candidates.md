# Spec: Admin View Approved Candidates

## Overview
Admins can view all approved candidate applications in one place to inspect the finalized candidate pool.

## Depends on
07-candidate-admin-approval

## Routes
- `GET /admin/candidates/approved` - list approved candidates - admin

## Database changes
No database changes.

## Templates
- Create: `templates/admin_candidates_approved.html`
- Modify: `templates/admin_dashboard.html` to link to approved candidates

## Files to change
- `app.py`
- `templates/admin_dashboard.html`

## Files to create
- `templates/admin_candidates_approved.html`

## New dependencies
No new dependencies

## Rules for implementation
- Use `admin_guard`.
- Query only `approval_status = 'APPROVED'`.
- Include candidate name, election title, and application date.
- Use existing admin table/card styling.
- Parameterize all SQL.

## Definition of done
- Admins can open `/admin/candidates/approved`.
- Only approved applications are listed.
- The dashboard links to the page.
- Non-admin users cannot access the route.
- UI matches the pending candidates page style.
