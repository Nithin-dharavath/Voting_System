# Spec: Election Results

## Overview
This feature allows admins to view and publish results for ended elections, and allows students to view published results. Vote counts remain hidden from students until the admin explicitly publishes the results. The `elections.result_published` boolean field already exists in the database and is used to gate visibility.

## Depends on
12-student-specific-active-election-vote, 13-upload-selfie-or-signature

## Routes
- `GET /admin/elections/{id}/results` — Admin view of vote tallies for an ended election (admin only)
- `POST /admin/elections/{id}/publish-results` — Toggle `result_published` on the election (admin only)
- `GET /student/elections/{id}/results` — Student view of published results (public; only if `result_published = true`)

## Database changes
No schema changes. The `elections` table already has a `result_published` boolean column (default false). Vote counts are computed via `SELECT COUNT(*) ... GROUP BY candidate_id` on the existing `votes` table, joined with `candidate_applications` and `users` to display candidate names.

## Templates
- **Create:** `templates/admin/election_results.html`
- **Create:** `templates/student/election_results.html`
- **Modify:** `templates/admin_elections_list.html` (add "Results" button/link for ENDED elections)
- **Modify:** `templates/admin_election_detail.html` (add "View Results" and "Publish Results" actions for ENDED elections)
- **Modify:** `templates/student_election_detail.html` (add "View Results" link when election is ENDED and `result_published = true`)

## Files to change
- `app.py`

## Files to create
- `templates/admin/election_results.html`
- `templates/student/election_results.html`

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
- Vote count queries must use `COUNT(*)` on `votes` grouped by `candidate_id`.
- The admin results page must show: candidate name (from `users`), candidate manifesto, vote count, and optionally vote percentage.
- The publish-results route must set `elections.result_published = true` only if the election status is `ENDED`.
- The student results page must 404 or redirect if `result_published` is false or if the election is not `ENDED`.
- Do NOT expose vote counts to students via any other route, including the election detail page or API.
- The admin results page should be accessible even before publishing, but the student page only after publishing.

## Definition of done
- Admin can view vote tallies for any ended election from the admin election list or detail page.
- Admin can click "Publish Results" on an ended election, which sets `result_published = true`.
- After publishing, students can view the results page for that election via a link on the election detail page.
- The student results page shows candidate names, vote counts, and percentages only if `result_published = true`.
- Unpublishing (setting `result_published = false`) is not required for this step.
- Students cannot see vote counts through any other route before publication.
