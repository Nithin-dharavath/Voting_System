# Spec: Profile

## Overview
Students and admins get read-only profile pages with identity details, role-specific activity, and optional profile icons.

## Depends on
- 02-login
- 04-admin-election
- 06-candidate-application
- 07-candidate-admin-approval

## Routes
- `GET /student/profile` - student profile and application status filter - logged-in student
- `GET /admin/profile` - admin profile and created-election summary - admin
- `GET /student/profile/icon` - stream student icon or placeholder - logged-in student
- `GET /admin/profile/icon` - stream admin icon or placeholder - admin
- `POST /student/profile/icon` - upload student icon - logged-in student
- `POST /admin/profile/icon` - upload admin icon - admin

## Database changes
Create `profile_icons`:

- `user_id` BIGINT primary key, FK to `users.id`, cascade delete
- `file_path` VARCHAR(512) not null
- `updated_at` DATETIME not null, default current timestamp

## Templates
- Create: `templates/student_profile.html`
- Create: `templates/admin_profile.html`
- Modify: `templates/student_dashboard.html` to link to `/student/profile`
- Modify: `templates/admin_dashboard.html` to link to `/admin/profile`

## Files to change
- `app.py`
- `templates/student_dashboard.html`
- `templates/admin_dashboard.html`

## Files to create
- `templates/student_profile.html`
- `templates/admin_profile.html`

## New dependencies
No new dependencies

## Rules for implementation
- Profile details are read-only except icon upload.
- Use existing `student_guard` and `admin_guard`.
- Student application filter uses `?status=APPROVED|PENDING|REJECTED`; no status means all.
- Admin profile lists elections where `elections.created_by` is the admin.
- Accept only PNG, JPG/JPEG, or WEBP icons.
- Safely rename files, store under configured uploads path, and persist only `file_path`.
- Protect upload POST routes with CSRF validation if the app has CSRF support.
- Use parameterized SQL and CSS variables.

## Definition of done
- Student profile shows identity, role, created date, icon, and filtered application list.
- Admin profile shows identity, role, created date, icon, and created-election summary.
- Upload routes reject non-images and store valid icons safely.
- Icon GET routes return uploaded icon or a placeholder.
- Role mismatches redirect to the proper area.
- Unauthenticated users redirect to `/login` or `/admin/login` as appropriate.
