# Spec: Candidate Admin Approval

## Overview
Admins review student candidate applications and approve or reject them before an election becomes active.

## Depends on
06-candidate-application

## Routes
- `GET /admin/candidates/pending` - list pending applications - admin
- `POST /admin/candidates/{id}/approve` - approve application - admin
- `POST /admin/candidates/{id}/reject` - reject application - admin
- `GET /admin/elections/{id}/candidates` - list applications for one election - admin

## Database changes
No database changes. Update `candidate_applications.approval_status` and `reviewed_by`.

## Templates
- Create: `templates/admin_candidates_pending.html`
- Create: `templates/admin_election_candidates.html`
- Modify: `templates/admin_dashboard.html` to link to pending review

## Files to change
- `app.py`
- `templates/admin_dashboard.html`

## Files to create
- `templates/admin_candidates_pending.html`
- `templates/admin_election_candidates.html`

## New dependencies
No new dependencies

## Rules for implementation
- Use `admin_guard` for all routes.
- Protect POST routes with CSRF validation if the app has CSRF support.
- Only transition `PENDING` applications.
- Set `reviewed_by` to the acting admin.
- Use parameterized SQL.

## Definition of done
- Admins can view pending candidate applications.
- Approve changes status to `APPROVED` and records `reviewed_by`.
- Reject changes status to `REJECTED` and records `reviewed_by`.
- Admins can view applications for a specific election.
- Non-admin users cannot access these routes.
