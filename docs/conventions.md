# Project Conventions

This document outlines the development conventions and guardrails for the Online Voting System.

## General Development Workflow
Follow the feature checklist for every change:
`Add route -> Add validation -> Add database operation -> Add error handling -> Add minimal test -> Update matching docs`

## Naming Conventions
### Database Fields
- Use the following field names consistently: `student_id`, `election_id`, `candidate_application_id`, `approval_status`, `result_published`, `verification_type`, `file_path`, `created_at`.

### Constants/Values
- **Roles**: `STUDENT`, `ADMIN`
- **Election Status**: `UPCOMING`, `ACTIVE`, `ENDED`
- **Candidate Status**: `PENDING`, `APPROVED`, `REJECTED`
- **Verification Types**: `SELFIE`, `SIGNATURE`

## Agent Guardrails
- Do not rename folders casually.
- Do not duplicate routes.
- Do not bypass backend validation.
- Do not split into microservices.
- Do not add new frameworks unless required.
- Do not edit `venv` or `__pycache__`.
- Keep documentation updated when routes, tables, or workflows change.

## Implementation Rules
- **Database**: Use `get_db_cursor()` for connection management.
- **Configuration**: Do not hardcode database passwords, JWT secrets, upload paths, or admin credentials. Use `.env` or environment variables.
- **Security**: 
    - All passwords must be hashed using `werkzeug.security`.
    - Session tokens must be stored in `HttpOnly`, `SameSite=Lax` cookies.
- **Uploads**:
    - Validate file types.
    - Rename uploaded files to avoid collisions.
    - Store only the `file_path` in the database.
