---
# Spec: Profile (User and Admin)

## Overview
This feature adds read-only profile pages for both students and administrators. The student profile surfaces identity details (name, email, profile icon) along with an elections filter that lists the student's candidate applications bucketed into `APPROVED`, `PENDING`, and `REJECTED` status, and other relevant activity information (e.g. account metadata). The admin profile surfaces the admin's identity details and a summary of elections they have created or moderated. These pages give users a single place to inspect their own state in the system without depending on the public dashboards.

## Depends on
- 02-login
- 04-admin-election
- 05-student-election-list
- 06-candidate-application
- 07-candidate-admin-approval

## Routes
- `GET /student/profile` — Render the student profile page with personal details, profile icon, and elections filtered by candidate application status (`PENDING`, `APPROVED`, `REJECTED`) — logged-in student
- `GET /admin/profile` — Render the admin profile page with personal details, profile icon, and a summary of created elections and moderation activity — admin
- `GET /student/profile/icon` — Stream the student's profile icon image — logged-in student
- `GET /admin/profile/icon` — Stream the admin's profile icon image — admin
- `POST /student/profile/icon` — Upload or replace the student's profile icon (multipart form, image only, safe renamed filename, store only `file_path`) — logged-in student
- `POST /admin/profile/icon` — Upload or replace the admin's profile icon (multipart form, image only, safe renamed filename, store only `file_path`) — admin

## Database changes
Add a new table:

- `profile_icons`
  - `user_id` (BIGINT, PK, FK -> users.id, ON DELETE CASCADE)
  - `file_path` (VARCHAR(512), NOT NULL)
  - `updated_at` (DATETIME, NOT NULL, default CURRENT_TIMESTAMP)

No new enum values. The `users` table is reused for identity fields (`full_name`, `email`, `department`, `academic_year`, `role`, `created_at`). The `candidate_applications` table (`approval_status` ∈ {`PENDING`, `APPROVED`, `REJECTED`}) is reused to power the student elections filter. The `elections` table (`created_by`) is reused to power the admin elections summary.

If a `profile_icons` directory does not already exist under `uploads/`, ensure it is created at runtime via configuration (no hardcoded path).

## Templates
- **Create:** `templates/student_profile.html`
- **Create:** `templates/admin_profile.html`
- **Modify:** `templates/student_dashboard.html` — add a link to `/student/profile`.
- **Modify:** `templates/admin_dashboard.html` — add a link to `/admin/profile`.

## Files to change
- `app.py`

## Files to create
- `templates/student_profile.html`
- `templates/admin_profile.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs.
- Parameterised queries only via `get_db_cursor()`.
- Passwords hashed with `werkzeug`.
- Use CSS variables, never hardcode hex values.
- All templates extend `base.html`.
- Do not hardcode database passwords, JWT secrets, upload paths, server URLs, or admin credentials. Use `.env` or environment variables.
- Validate uploaded file types (PNG/JPG/WEBP only), rename uploaded files safely (e.g. `user_<id>_<uuid>.<ext>`), and store only `file_path` in the database.
- Keep changes minimal and aligned with the existing app structure.
- Do not introduce new architecture unless the spec explicitly requires it.
- Profile pages are read-only aside from the icon upload. No editing of name/email/department/year in this step.
- All POST routes (icon uploads) must be protected by CSRF validation.
- Sessions and access are enforced via existing `student_guard` and `admin_guard` dependencies.
- The student elections filter must be implemented as a query-string filter (`?status=APPROVED|PENDING|REJECTED`) with all three statuses available; no value defaults to a combined "all" view.

## Definition of done
- Authenticated student can navigate to `/student/profile` from the student dashboard.
- Student profile shows `full_name`, `email`, `department`, `academic_year`, `role`, `created_at`, and a profile icon placeholder or uploaded icon.
- Student profile lists the student's candidate applications grouped/filterable by `approval_status` (`APPROVED`, `PENDING`, `REJECTED`); each entry shows the linked election title and the application timestamp.
- Authenticated admin can navigate to `/admin/profile` from the admin dashboard.
- Admin profile shows `full_name`, `email`, `role`, `created_at`, and a profile icon placeholder or uploaded icon.
- Admin profile lists the elections the admin has created (via `elections.created_by`) with title, status, and start/end times.
- An unauthenticated user is redirected to `/login` when accessing either profile route.
- A student accessing `/admin/profile` is redirected to the student area, and an admin accessing `/student/profile` is redirected to the admin area.
- `POST /student/profile/icon` and `POST /admin/profile/icon` accept a single image upload, reject non-image MIME types, store the file under `uploads/profiles/` (path resolved via env config), and persist the path in `profile_icons`.
- `GET /student/profile/icon` and `GET /admin/profile/icon` return the uploaded icon if present, or a default placeholder otherwise.
- All new routes reuse existing guard dependencies; no new auth flow is introduced.
- All new templates extend `base.html` and use CSS variables for colors.
