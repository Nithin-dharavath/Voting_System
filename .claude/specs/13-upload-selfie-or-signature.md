# Spec: Upload Selfie or Signature

## Overview
This feature implements the final step of the voting process. After a student selects a candidate, they must upload a verification document (either a selfie or a signature) to prove their identity. The vote is only committed to the database once the verification is successfully uploaded, ensuring that every vote is backed by audit evidence.

## Depends on
12-student-specific-active-election-vote

## Routes
- `GET /student/elections/{id}/verify` — Renders the verification upload page. — logged-in student
- `POST /student/elections/{id}/verify` — Processes the file upload, records the verification, and commits the vote in a single transaction. — logged-in student

## Database changes
No database schema changes required. The feature will utilize the existing `vote_verifications` table.
In plan mode - provied columns need to be create in database - table name and its columns - follow the singular naming

## Templates
- **Create:** `templates/student_election_verify.html`
- **Modify:** `templates/student_election_vote.html` (Update form action to point to the verification step if necessary, or handle the flow via redirects).

## Files to change
- `app.py`

## Files to create
- `templates/student_election_verify.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs.
- Parameterised queries only.
- Passwords hashed with `werkzeug`.
- Use CSS variables, never hardcode hex values.
- All templates extend `base.html`.
- Do not hardcode database passwords, JWT secrets, upload paths, server URLs, or admin credentials.
- Validate uploaded files (only image formats: .jpg, .jpeg, .png), rename them safely, and store only file paths.
- **Atomic Transaction**: The final vote commit must be an ACID transaction:
    1. Validate voting session is still active and not completed.
    2. Insert the record into the `votes` table.
    3. Insert the record into the `vote_verifications` table.
    4. Update the `voting_sessions` table to set `completed = 1`.
    5. Commit the transaction.
- If any step in the transaction fails, a `ROLLBACK` must be performed to prevent partial votes.
- Keep changes minimal and aligned with the existing app structure.
- Do not introduce new architecture unless the spec explicitly requires it.

## Definition of done
- A student can reach the verification page after submitting their candidate choice.
- The verification page allows selecting between "Selfie" and "Signature" and uploading a file.
- Uploading a non-image file returns a validation error.
- Upon successful upload, the vote and verification are recorded in the database, the session is marked as completed, and the user is redirected to the election detail page with a success message.
- Verifying the database shows that a record exists in both `votes` and `vote_verifications` for the successful vote.
- Attempting to vote again for the same election after successful verification is blocked.
