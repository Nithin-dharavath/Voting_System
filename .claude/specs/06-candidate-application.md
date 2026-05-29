---
# Spec: Candidate Application

## Overview
This feature allows students to apply as candidates for upcoming elections. Students provide a manifesto, and their application remains in a `PENDING` state until an administrator reviews and either approves or rejects it. This is a critical step in the election lifecycle, as only `APPROVED` candidates can receive votes.

## Depends on
05-student-election-list

## Routes
- `GET /student/elections/{id}/apply` — Application form for a specific election — Logged-in Student
- `POST /candidates/apply` — Submit candidate application — Logged-in Student
- `GET /student/candidate-status` — View status of all the student's candidate applications — Logged-in Student

## Database changes
No new tables needed. Use the `candidate_applications` table as defined in `docs/database.md`:
- `id` (PK)
- `user_id` (FK to `users`)
- `election_id` (FK to `elections`)
- `manifesto` (TEXT)
- `approval_status` (ENUM: 'PENDING', 'APPROVED', 'REJECTED')
- `reviewed_by` (FK to `users`, nullable)
- `applied_at` (TIMESTAMP)

Constraints:
- Unique constraint on `(user_id, election_id)` to prevent multiple applications for the same election.

## Templates
- **Create:** 
    - `templates/student_election_apply.html` — Form to submit manifesto and application.
    - `templates/student_candidate_status.html` — Page listing the student's applications and their current statuses.
- **Modify:** 
    - `templates/student_election_detail.html` — Add a link/button to "Apply as Candidate" if the election is `UPCOMING` and the user hasn't already applied.

## Files to change
- `app.py` — Implement the new routes and business logic.

## Files to create
- `templates/student_election_apply.html`
- `templates/student_candidate_status.html`

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
- **Business Logic Constraints:**
    - Students can only apply for elections with status `UPCOMING`.
    - Students cannot apply if they have already submitted an application for that election.
    - Students cannot re-apply if their previous application was `REJECTED`.
    - Application status must default to `PENDING`.

## Definition of done
- [ ] Student can navigate to `/student/elections/{id}/apply` for an `UPCOMING` election.
- [ ] Student can submit a manifesto via the application form.
- [ ] Application is correctly inserted into `candidate_applications` with status `PENDING`.
- [ ] Application is prevented if the election is `ACTIVE` or `ENDED`.
- [ ] Application is prevented if the student has already applied to that election.
- [ ] Student can view their application status on `/student/candidate-status`.
- [ ] "Apply as Candidate" button appears on the election detail page only when eligible.
---
