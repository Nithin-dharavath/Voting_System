# Phase 5: Setup Student Election View

## Goal
Allow students to view elections and interact based on election status.

## To Do
- Create student election list page `/student/elections`.
- Create election detail page `/student/elections/:id`.
- Display all available elections to students.
- Show election details:
  - `title`
  - `description`
  - `start_time`
  - `end_time`
  - `status`
- Add election status handling:
  - `UPCOMING`
  - `ACTIVE`
  - `ENDED`
- Show upcoming elections section.
- Show active elections section.
- Show ended elections section.
- Add action buttons based on election status:
  - `UPCOMING → Apply as Candidate`
  - `ACTIVE → Vote`
  - `ENDED → View Result`
- Create route to fetch single election details `GET /elections/:id`.
- Restrict student pages access to authenticated students only.
- Test student dashboard access.
- Test election listing for students.
- Test election detail page.
- Test election status visibility.
- Test action button rendering logic.

## End Result
Students can view elections, check election status, and access appropriate actions successfully.