# Spec: Candidate Application

## Overview
Students can apply to become candidates for upcoming elections. Applications remain `PENDING` until admin review.

## Depends on
05-student-election-list

## Routes
- `GET /student/elections/{id}/apply` - render application form - logged-in student
- `POST /candidates/apply` - submit application - logged-in student
- `GET /student/candidate-status` - list the student's applications - logged-in student

## Database changes
No database changes. Use `candidate_applications` with unique `(user_id, election_id)`.

## Templates
- Create: `templates/student_election_apply.html`
- Create: `templates/student_candidate_status.html`
- Modify: `templates/student_election_detail.html` to show Apply when eligible

## Files to change
- `app.py`
- `templates/student_election_detail.html`

## Files to create
- `templates/student_election_apply.html`
- `templates/student_candidate_status.html`

## New dependencies
No new dependencies

## Rules for implementation
- Only `STUDENT` users can apply.
- Election must be `UPCOMING`.
- A student can apply once per election.
- Previously rejected students cannot re-apply for the same election.
- New applications default to `PENDING`.
- Use parameterized SQL and existing guards.

## Definition of done
- Eligible students can open the apply page and submit a manifesto.
- Ineligible election statuses are blocked.
- Duplicate applications are blocked.
- Submitted applications are stored as `PENDING`.
- `/student/candidate-status` shows each application and status.
- Apply button appears only when the student is eligible.
