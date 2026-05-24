# Phase 4: Setup Admin Election Creation

## Goal
Allow admins to create and manage elections.

## To Do
- Create admin dashboard page `/admin/dashboard`.
- Create election list page `/admin/elections`.
- Create election create page `/admin/elections/create`.
- Create `elections` table.
- Add election fields:
  - `id`
  - `title`
  - `description`
  - `start_time`
  - `end_time`
  - `result_published`
  - `created_by`
- Create election create route `POST /elections`.
- Create election list route `GET /elections`.
- Add election status handling:
  - `UPCOMING`
  - `ACTIVE`
  - `ENDED`
- Test election creation.
- Test election listing.
- Test election status logic.
- Restrict election creation access to admins only.

## End Result
Admins can create and view elections successfully.