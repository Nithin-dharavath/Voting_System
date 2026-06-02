# Spec: Profile Page

## Overview
The Profile Page feature allows users (both Students and Admins) to view and manage their personal information. It provides a centralized way for users to update their details and for admins to manage user profiles, enhancing the personalized experience and administrative control within the Online Voting System.

## Depends on
None

## Routes
- `GET /profile` — View and edit current user's profile — logged-in
- `POST /profile/update` — Update current user's profile details and picture — logged-in
- `GET /admin/users/{id}/profile` — View a specific user's profile — admin
- `POST /admin/users/{id}/update` — Update a specific user's profile details — admin

## Database changes
- Add `profile_picture` column to `users` table: `VARCHAR(255) DEFAULT NULL`.

## Templates
- **Create:**
    - `templates/profile.html` — User's own profile view and edit form.
    - `templates/admin_user_profile.html` — Admin's view and edit form for a specific user.
- **Modify:**
    - `templates/base.html` — Add a "Profile" link in the navigation bar for logged-in users.

## Files to change
- `app.py` — Implement new routes and profile update logic.

## Files to create
- `templates/profile.html`
- `templates/admin_user_profile.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs.
- Parameterised queries only.
- Passwords hashed with `werkzeug`.
- Use CSS variables, never hardcode hex values.
- All templates extend `base.html`.
- Do not hardcode database passwords, JWT secrets, upload paths, server URLs, or admin credentials.
- Validate uploaded profile pictures (e.g., `.jpg`, `.jpeg`, `.png`), rename them safely, and store only the `file_path` in the database.
- Store profile images in `/uploads/profiles/`.
- Keep changes minimal and aligned with the existing app structure.
- Do not introduce new architecture unless the spec explicitly requires it.

## Definition of done
- [ ] A logged-in user can access `/profile` and see their current details.
- [ ] A logged-in user can update their name, department, academic year, and profile picture.
- [ ] Profile pictures are successfully uploaded, renamed, and displayed.
- [ ] An admin can access `/admin/users/{id}/profile` and see any user's details.
- [ ] An admin can update any user's profile details.
- [ ] Non-logged-in users are redirected to `/login` when accessing `/profile`.
- [ ] Non-admin users are redirected to `/admin/login` or their dashboard when accessing admin profile routes.
- [ ] Navigation bar contains a working "Profile" link when authenticated.
