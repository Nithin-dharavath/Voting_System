# Spec: Profile Management Extension

## Overview
This extends the read-only profile work from step 09 by allowing users to update limited profile fields and allowing admins to inspect or update user profiles.

## Depends on
09-profile

## Routes
- `GET /profile` - redirect current user to the correct role profile - logged-in
- `POST /profile/update` - update the current user's allowed fields - logged-in
- `GET /admin/users/{id}/profile` - view a user's profile - admin
- `POST /admin/users/{id}/update` - update allowed fields for a user - admin

## Database changes
No new database changes if step 09 uses `profile_icons`. Do not add a duplicate `profile_picture` column unless the existing schema already uses it.

## Templates
- Modify: `templates/student_profile.html`
- Modify: `templates/admin_profile.html`
- Create: `templates/admin_user_profile.html`
- Modify: `templates/base.html` for a role-aware Profile link if missing

## Files to change
- `app.py`
- `templates/base.html`
- `templates/student_profile.html`
- `templates/admin_profile.html`

## Files to create
- `templates/admin_user_profile.html`

## New dependencies
No new dependencies

## Rules for implementation
- Keep allowed editable fields explicit: `full_name`, `department`, `academic_year`, and profile icon where applicable.
- Do not let users change role, email, password, `is_active`, or audit fields in this step.
- Admin updates must use `admin_guard`.
- Use parameterized SQL.
- Validate uploads through the step 09 icon rules.
- Reuse existing templates and CSS variables.

## Definition of done
- Logged-in users can open `/profile` and reach their role-specific profile.
- Users can update only allowed fields.
- Admins can view and update allowed fields for another user.
- Unauthorized users cannot access admin profile-management routes.
- Navigation includes a working role-aware Profile link.
