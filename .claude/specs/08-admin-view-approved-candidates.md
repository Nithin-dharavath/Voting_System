# Spec: Admin View Approved Candidates List

## Overview
This feature allows administrators to view a comprehensive list of all candidates who have been approved for various elections. This provides the administrator with a clear overview of the finalized candidate pool, complementing the existing pending applications view.

## Depends on
07-candidate-admin-approval

## Routes
- `GET /admin/candidates/approved` — List of all candidates with 'APPROVED' status — admin

## Database changes
No database changes.

## Templates
- **Create:** `templates/admin_candidates_approved.html`
- **Modify:** `templates/admin_dashboard.html` — Add navigation link to the approved candidates list.

## Files to change
- `app.py`

## Files to create
- `templates/admin_candidates_approved.html`

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
- Admin can access `/admin/candidates/approved` and see a table of approved candidates.
- The table displays the candidate's full name, the election they applied for, and the application date.
- Only candidate applications with `approval_status = 'APPROVED'` are listed.
- The route is protected by the `admin_guard` dependency.
- The admin dashboard contains a link to this view.
- The UI is consistent with the existing `admin_candidates_pending.html` template.
