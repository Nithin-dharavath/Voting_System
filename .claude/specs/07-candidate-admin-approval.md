# Spec: Candidate Admin Approval

## Overview
This feature enables administrators to review, approve, or reject student applications to become candidates in an election. This is a critical step in the election lifecycle, ensuring that only qualified students can run for office before the election is set to `ACTIVE`.

## Depends on
06-candidate-application

## Routes
- `GET /admin/candidates/pending` — List all candidate applications with `PENDING` status — Admin
- `POST /admin/candidates/{id}/approve` — Update application status to `APPROVED` — Admin
- `POST /admin/candidates/{id}/reject` — Update application status to `REJECTED` — Admin
- `GET /admin/elections/{id}/candidates` — View all applications for a specific election — Admin

## Database changes
No database changes. Uses existing `candidate_applications` table.
- Update `approval_status` to `APPROVED` or `REJECTED`.
- Update `reviewed_by` with the `user_id` of the admin.

## Templates
- **Create:**
    - `templates/admin_candidates_pending.html` — Page to review and action pending applications.
    - `templates/admin_election_candidates.html` — Page to view all candidates for a specific election.
- **Modify:**
    - `templates/admin_dashboard.html` — Add link to the pending candidates review page.

## Files to change
- `app.py`

## Files to create
- `templates/admin_candidates_pending.html`
- `templates/admin_election_candidates.html`

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
- Ensure all POST routes are protected by `verify_csrf`.
- Use `admin_guard` for all routes.
- The `reviewed_by` field must be updated to reflect the admin who took the action.

## Definition of done
- [ ] Admin can access `/admin/candidates/pending` and see a list of students who have applied as candidates.
- [ ] Admin can approve a candidate, resulting in `approval_status = 'APPROVED'` and the admin's ID in `reviewed_by`.
- [ ] Admin can reject a candidate, resulting in `approval_status = 'REJECTED'` and the admin's ID in `reviewed_by`.
- [ ] Admin can view all candidates for a specific election via `/admin/elections/{id}/candidates`.
- [ ] CSRF tokens are correctly implemented and validated for approve/reject actions.
- [ ] Application correctly redirects to the pending list or election candidate list after an action.
- [ ] Non-admin users are redirected to `/admin/login` when attempting to access these routes.
