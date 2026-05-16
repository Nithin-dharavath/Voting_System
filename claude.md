# Online Voting System

Medium-level online voting system for an educational institution. Students register/login, apply as candidates, vote in active elections, upload verification, and view published results. Admins create elections, review candidates, monitor voting, and publish results.

## Project Structure

```text
Voting_System/
+-- .claude/        agents, commands, skills, specs, settings.local.json
+-- .codex/         Codex config
+-- database/       DB connection, schema, seed, helpers
+-- docs/           api-contracts.md, conventions.md, database.md, project-overview.md
+-- static/         CSS, JS, images, icons
+-- templates/      HTML pages/templates
+-- tests/          Route, DB, workflow, security tests
+-- uploads/        selfie, signature, manifesto, profile uploads
+-- venv/           local Python environment; do not edit
+-- __pycache__/    generated Python cache; do not edit
+-- .gitignore
+-- app.py          main FastAPI entry point
+-- README.md
```

## Read Before Coding

Agents must check:

```text
README.md
docs/project-overview.md
docs/database.md
docs/api-contracts.md
docs/conventions.md
app.py
```

Before adding code, verify current route names, folder names, app framework style, database config source, table names, field names, and existing user changes.

## Main Workflow

```text
Student registers -> Student logs in -> Admin logs in -> Admin creates election
-> Student views election -> Student applies as candidate
-> Admin approves/rejects candidate -> Election becomes active
-> Student starts voting session -> Student selects candidate
-> Student uploads verification -> Student submits vote
-> Election ends -> Admin publishes result -> Student views result
```

## Planned Modules

```text
Authentication, Users, Elections, Candidates, Voting Sessions,
Vote Verification, Vote Submission, Results, Audit Logs
```

## UI Routes

Public/student:

```text
/, /register, /login
/student/dashboard, /student/elections, /student/elections/:id
/student/elections/:id/apply, /student/candidate-status
/student/elections/:id/vote, /student/elections/:id/verification
/student/vote-success, /student/results, /student/results/:election_id
```

Admin:

```text
/admin/login, /admin/dashboard
/admin/elections, /admin/elections/create, /admin/elections/:id
/admin/candidates, /admin/elections/:id/candidates
/admin/results, /admin/results/:election_id, /admin/audit
```

## API Routes

```text
Auth: POST /auth/register, POST /auth/login, GET /auth/me
Users: GET /users/me
Elections: POST /elections, GET /elections, GET /elections/{id}, PUT /elections/{id}, DELETE /elections/{id}
Candidates: POST /candidates/apply, GET /candidates/my-applications, GET /candidates/election/{election_id}, GET /candidates/election/{election_id}/approved
Admin Candidates: GET /admin/candidates/pending, GET /admin/elections/{election_id}/candidates, PUT /admin/candidates/{application_id}/approve, PUT /admin/candidates/{application_id}/reject
Voting: POST /votes/session/start, GET /votes/session/{election_id}, POST /votes/submit, GET /votes/status/{election_id}
Verification: POST /verification/upload
Results: GET /results/{election_id}, POST /results/{election_id}/publish, GET /results/published, GET /results/{election_id}/public
Audit: GET /admin/audit/logs
```

## Database

Tables:

```text
users, elections, candidate_applications, voting_sessions,
votes, vote_verifications, audit_logs
```

Core rules:

```text
users.email unique
candidate_applications unique by user_id + election_id
votes unique by student_id + election_id
votes point to APPROVED candidates only
results hidden until result_published = true
```

## Required Naming

Fields:

```text
student_id, election_id, candidate_application_id, approval_status,
result_published, verification_type, file_path, created_at
```

Values:

```text
Role: STUDENT, ADMIN
Election: UPCOMING, ACTIVE, ENDED
Candidate: PENDING, APPROVED, REJECTED
Verification: SELFIE, SIGNATURE
```

## Connection / Config Rules

Before database or auth work, find where these come from:

```text
DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, JWT_SECRET, UPLOAD_DIR
```

Use `.env`, environment variables, or one central config file. Do not hardcode database passwords, JWT secrets, upload paths, server URLs, or admin credentials.

## Upload Rules

Folders:

```text
uploads/selfies/
uploads/signatures/
uploads/manifestos/
uploads/profiles/
```

Validate file type, rename uploaded files, store only `file_path` in the DB, and never trust the original filename.

## Voting Rules

```text
Election must be ACTIVE
Student must have active voting session
Student can vote once per election
Candidate must be APPROVED
Verification must exist before final vote
No new session if election has less than 2 minutes remaining
Vote transaction must rollback if any step fails
```

## Result Rules

```text
Admin can view counts after election ends
Students cannot view live counts
Students see results only after admin publishes
Visibility is controlled by result_published
```

## Agent Guardrails

```text
Do not rename folders casually
Do not duplicate routes
Do not bypass backend validation
Do not split into microservices
Do not add new frameworks unless required
Do not edit venv or __pycache__
Keep docs updated when routes/tables/workflow change
```

Feature checklist:

```text
Add route -> Add validation -> Add database operation
-> Add error handling -> Add minimal test -> Update matching docs
```

## Run Note

If `app.py` exposes `app = FastAPI()`, run locally with:

```text
uvicorn app:app --reload
```
