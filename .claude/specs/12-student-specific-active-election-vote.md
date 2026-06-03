# Spec: Student Specific Active Election Vote

## Overview
This feature allows an authenticated student to open a specific active election, view only the approved candidates for that election, and submit a single vote. It is the first concrete voting step for students and must enforce election timing, candidate eligibility, and one-vote-per-student rules at the backend.

## Depends on
- 05-student-election-list
- 07-candidate-admin-approval

## Routes
- `GET /student/elections/{id}/vote` - Show the vote page for one active election with its approved candidates - logged-in student
- `POST /student/elections/{id}/vote` - Submit one vote for a selected approved candidate in that active election - logged-in student

## Database changes
Use the existing voting tables described in `docs/database.md`.

- `votes`
  - `student_id`
  - `election_id`
  - `candidate_application_id`
  - `voted_at`
- `voting_sessions`
  - `student_id`
  - `election_id`
  - `started_at`
  - `expires_at`
  - `completed`

Use the existing `candidate_applications` table to load candidate options, but only rows with `approval_status = 'APPROVED'` for the requested election.

Constraints and behavior:
- Enforce one vote per student per election with the existing `votes` uniqueness rule on `(student_id, election_id)`.
- Reject voting when the election status is not `ACTIVE`.
- Reject voting if the selected candidate does not belong to the same election.
- Reject voting if the selected candidate is not `APPROVED`.
- If `voting_sessions` is already used in the app by the time of implementation, mark the session as completed after a successful vote. If it is not yet wired in product code, keep the vote flow minimal and consistent with the documented table design.

## Templates
- **Create:** `templates/student_election_vote.html`
- **Modify:** `templates/student_election_detail.html` - Add a "Vote Now" action only when the election is `ACTIVE` and the student is still eligible to vote.

## Files to change
- `app.py`

## Files to create
- `templates/student_election_vote.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs.
- Use `get_db_cursor()` and parameterized SQL.
- Hash passwords with `werkzeug.security`.
- Use CSS variables from `static/css/style.css`.
- All templates extend `base.html`.
- Store secrets and paths in environment/config.
- Validate uploads, safely rename files, store only file paths.
- Keep changes minimal and aligned with the existing app.
- Only students can access the vote page and submit a vote.
- Only `APPROVED` candidates for the current election may be displayed or accepted.
- The backend must re-check election status and prior voting before inserting a vote, even if the UI already hides the action.
- The vote form must not expose or rely on live vote counts.

## Definition of done
- A logged-in student can open `/student/elections/{id}/vote` for an `ACTIVE` election and see the approved candidate list for that election only.
- A student cannot open the vote page for `UPCOMING` or `ENDED` elections.
- A student cannot submit a vote for a candidate from another election or for a candidate that is not `APPROVED`.
- After one successful submission, the student cannot vote again in the same election.
- Unauthenticated users are redirected away from both vote routes.
- The election detail page shows a visible voting action only when the election is `ACTIVE` and the student has not already voted.
