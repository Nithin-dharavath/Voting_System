# Spec: Vote Counting and Publishing

## Overview
This feature provides admins with a centralized overview of vote counts across all ended elections, and gives students a dedicated page to browse all elections whose results have been published. Vote counts are computed on-the-fly via SQL aggregation against the `votes` table and are never exposed to students before the admin explicitly publishes results. The `result_published` boolean on `elections` gates student visibility.

## Depends on
14-election-results

## Routes
- `GET /admin/results` — Admin overview of all ended elections with vote tallies (admin only)
- `POST /admin/elections/{id}/publish-results` — Publish results for a specific ended election (admin only)
- `GET /student/results` — Student overview of all published election results (logged-in student)

## Database changes
No schema changes. Uses existing `elections` (with `result_published` column), `votes`, `candidate_applications`, and `users` tables.

## Templates
- **Create:** `templates/admin_results.html`
- **Create:** `templates/student_results.html`
- **Modify:** `templates/base.html` — Add "View All Results" nav link for admins (pointing to `/admin/results`) and for students (pointing to `/student/results`)

## Files to change
- `app.py`

## Files to create
- `templates/admin_results.html`
- `templates/student_results.html`

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
- Vote counts must be computed via `COUNT(*)` on `votes` grouped by `candidate_id`, never cached in a column.
- The admin overview must show: election title, total valid votes per candidate, candidate name, department, vote percentage, and a publish/unpublish action if not yet published.
- The student overview must only show elections where `result_published = 1` and `status = 'ENDED'`.
- Students must never see vote counts via any route other than the dedicated results pages after the admin has published.
- The publish action must set `elections.result_published = 1`.

## Definition of done
- Admin can visit `/admin/results` and see a list of all ended elections with vote counts per candidate.
- Admin can publish or unpublish results from the overview page.
- Students can visit `/student/results` and see only elections with published results.
- Students cannot see results for unpublished elections via the overview or any other route.
- Nav links for both admin and student results pages are present in the base template.
