# Phase 3 Implementation Plan: Features & Usability

Phase 3 covers 15 discrete improvements across 3 categories. Total estimated effort: **3-4 weeks**.

---

## Part A: System Maintenance (Foundation)

### A1. Database Migration System *(2-3 days)*
- Install Alembic, run `alembic init alembic`
- Configure `alembic/env.py` to read DB connection from existing `database/connection.py`
- Create initial migration that reflects current `schema.sql` (autogenerate)
- Add `alembic.ini` to project root
- Future migrations for Phase 3 schema changes (audit_log table, etc.)
- **Files:** `alembic/` (new), `alembic.ini` (new), `requirements.txt` (add alembic)

### A2. Configuration Management *(1 day)*
- Create `config.py` using `pydantic-settings` for type-safe env vars
- Centralize: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_HOURS`, `ENVIRONMENT`
- Add `DB_POOL_SIZE`, `UPLOAD_DIR`, `LOG_LEVEL` settings
- Update `.env.example` with all new variables
- Update `app.py` and `database/connection.py` to use `config.py`
- **Files:** `config.py` (new), `app.py:101-102`, `database/connection.py`, `.env.example`
- **Dependency:** `pydantic-settings` in `requirements.txt`

### A3. Health Check Endpoint *(0.5 day)*
- Add `GET /health` endpoint returning:
  - DB connectivity (ping test)
  - Uptime / version info
  - Disk space for uploads directory
- **Files:** `app.py` (new route)

### A4. Structured Logging *(1 day)*
- Enhance existing `RequestLoggingMiddleware` to use structured JSON format
- Add `LOG_LEVEL` config support
- Add request body logging for errors only (POST failures)
- Add response time percentiles
- **Files:** `middleware.py`, `config.py`, `app.py:62`

### A5. Error Tracking Integration *(1 day)*
- Add **Sentry** SDK (`sentry-sdk[fastapi]`)
- Initialize in `app.py` startup, gated by `SENTRY_DSN` env var
- Attach user context to Sentry events for authenticated requests
- **Files:** `app.py`, `requirements.txt`
- **Dependency:** `sentry-sdk[fastapi]` in `requirements.txt`

---

## Part B: User Experience

### B1. Password Strength Requirements *(2 days)*
*Already partially done: `main.js` has a frontend strength meter.*
- **Server-side:** Upgrade `auth_service.register_user` to enforce:
  - Min 8 chars -> min 12 chars
  - Require uppercase, lowercase, digit, special character
- **Frontend:** Enhance `setupPasswordStrength` in `main.js` to show:
  - Real-time requirements checklist (checkmark per met criterion)
  - Visual strength bar (weak/medium/strong/very-strong)
  - Block form submission if requirements not met
- **Files:** `services/auth_service.py:56-57`, `static/js/main.js`, `templates/register.html`

### B2. Password Breach Checking *(1 day)*
- Add `services/breach_service.py` with HIBP API client using k-anonymity model
- Call on registration & login (optional, configurable)
- Warn user if password is compromised (non-blocking on login, blocking on register)
- **Files:** `services/breach_service.py` (new), `services/auth_service.py`, `config.py`, `requirements.txt`

### B3. Improved Error Messaging & User Feedback *(2 days)*
- Replace current flash message system (query param -> dict) with proper session flash messages
- Or: enhance existing approach with categorized, auto-dismissing toasts
- Add inline field-level validation errors on forms (both client + server)
- Create reusable `partials/toast.html` for success/error/info/warning toasts
- Standardize error responses across all routes
- **Files:** `templates/partials/toast.html` (new), `templates/base.html`, `static/js/main.js`, `static/css/style.css`, all form templates

### B4. Loading States & Navigation *(2 days)*
- Add CSS loading spinner for form submits and page transitions
- Add `disabled` + spinner on submit buttons during form submission
- Improve navbar: highlight active page, add breadcrumb component
- Create `partials/breadcrumb.html` and add to admin pages
- Add "Back to top" button on long pages
- **Files:** `static/css/style.css`, `static/js/main.js`, `templates/partials/navbar.html`, `templates/partials/breadcrumb.html` (new), all admin templates

### B5. "Remember Me" Functionality *(2 days)*
- Add checkbox on login forms
- Create separate token configurations:
  - `REMEMBER_ME_EXPIRE_DAYS = 30` (configurable)
  - Normal: 24h expiry -> reduce to **1 hour** for better security
- Implement in `auth_service.create_access_token` with optional `remember_me` param
- Update `app.py` login routes to pass `remember_me` from form
- **Files:** `services/auth_service.py:30-34`, `config.py`, `app.py:243-271`, `templates/login.html`, `templates/admin-login.html`

---

## Part C: Administrative Features

### C1. Enhanced Dashboard with Real-Time Stats *(2-3 days)*
- Add new dashboard query methods to `services/election_service.py`:
  - `get_dashboard_stats()` -- total students, total elections, total votes, pending apps, turnout %
  - `get_vote_trend(days=7)` -- votes per day for chart
  - `get_recent_activity(limit=20)` -- expand from current 10
- Move inline dashboard query from `app.py:641-663` into service layer
- Add simple chart (bar chart of votes per election) using Chart.js or canvas-based rendering
- Update `admin_dashboard.html` with:
  - Better stat cards (icons, trend indicators)
  - Mini chart
  - Full recent activity feed with pagination
- **Files:** `services/election_service.py`, `services/vote_service.py`, `services/candidate_service.py`, `app.py:626-676`, `templates/admin_dashboard.html`, `static/js/main.js`, `static/css/style.css`, `templates/partials/dashboard_chart.html` (new)

### C2. Better Election Management UI *(2-3 days)*
- Add pagination to election list (server-side `LIMIT/OFFSET`)
- Add search/filter: by title, status, date range
- Add bulk actions: select multiple elections -> delete, publish results
- Add election cloning (duplicate with new dates)
- Improve election form: date-time picker, preview, confirmation dialog on delete
- Consolidate template styling (all admin pages use `modern-page-wrapper`)
- **Files:** `services/election_service.py`, `app.py:679-696`, `templates/admin_elections.html`, `templates/admin_election_create.html`, `templates/admin_election_edit.html`, `static/js/main.js`, `static/css/style.css`

### C3. Improved Candidate Management (Bulk Approval/Rejection) *(2 days)*
- Add checkboxes to candidate list table
- Add "Approve Selected" / "Reject Selected" buttons
- Add `POST /admin/candidates/bulk-action` route accepting list of IDs + action
- Add `services/candidate_service.bulk_update_candidate_status(ids, action, reviewer_id)`
- Improve candidate search: filter by election, department, date range
- **Files:** `services/candidate_service.py`, `app.py` (new route), `templates/admin_candidates_list.html`, `static/js/main.js`, `static/css/style.css`

### C4. Comprehensive Audit Logging *(3-4 days)*
- Create `audit_log` table in DB:
  ```sql
  CREATE TABLE audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id INT,
    details JSON,
    ip_address VARCHAR(45),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
  );
  ```
- Create Alembic migration for audit_log table
- Create `services/audit_service.py` with `log_action()` function
- Hook into all admin actions: election CRUD, candidate approval/rejection, results publishing, user profile edits, login/logout
- Create `GET /admin/audit` route with pagination + filters (by user, action, date range)
- Create `templates/admin_audit.html` -- table view with search
- Enable the disabled `/admin/audit` sidebar link
- **Files:** `database/schema.sql`, `alembic/versions/xxx_add_audit_log.py` (new), `services/audit_service.py` (new), `app.py` (new route + hooks), `templates/admin_audit.html` (new), `templates/partials/admin_sidebar.html`

### C5. Export Functionality (CSV/PDF) *(2-3 days)*
- **CSV export:** Add `GET /admin/elections/{id}/results/export?format=csv`
  - Use Python's `csv` module to stream results as CSV download
  - Headers: Candidate Name, Department, Year, Votes, Percentage
- **PDF export:** Add `GET /admin/elections/{id}/results/export?format=pdf`
  - Use `reportlab` or `weasyprint` for PDF generation
  - Include: election title, date, results table, winner highlight
- Add export buttons on `admin_election_results.html` and `admin_results.html`
- Add student-facing download on `student_election_results.html`
- **Files:** `services/export_service.py` (new), `app.py` (new route), `templates/admin_election_results.html`, `templates/admin_results.html`, `templates/student_election_results.html`, `requirements.txt` (add `reportlab` or similar)

---

## Implementation Order (Recommended)

| Step | Item | Depends On | Est. Days |
|------|------|-----------|-----------|
| 1 | A2 - Configuration Management | -- | 1 |
| 2 | A1 - Database Migrations | A2 | 2-3 |
| 3 | A3 - Health Check | A2 | 0.5 |
| 4 | A4 - Structured Logging | A2 | 1 |
| 5 | A5 - Error Tracking | A2 | 1 |
| 6 | B1 - Password Strength | A2 | 2 |
| 7 | B2 - Breach Checking | B1 | 1 |
| 8 | B3 - Error Messaging | -- | 2 |
| 9 | B5 - Remember Me | A2 | 2 |
| 10 | B4 - Loading States | -- | 2 |
| 11 | C4 - Audit Logging | A1, A2 | 3-4 |
| 12 | C1 - Dashboard | A1, C4 | 2-3 |
| 13 | C2 - Election Management | A1, C4 | 2-3 |
| 14 | C3 - Candidate Management | A1, C4 | 2 |
| 15 | C5 - Export | C2 | 2-3 |

---

## Key Files to Create
| File | Purpose |
|------|---------|
| `config.py` | Centralized pydantic-settings config |
| `alembic/` | Database migration framework |
| `services/audit_service.py` | Audit logging service |
| `services/breach_service.py` | HIBP password breach check |
| `services/export_service.py` | CSV/PDF export |
| `templates/admin_audit.html` | Audit log viewer page |
| `templates/partials/toast.html` | Reusable toast component |
| `templates/partials/breadcrumb.html` | Breadcrumb navigation |

## Key Files to Modify
| File | Changes |
|------|---------|
| `app.py` | +5 routes, hook audit into ~15 existing routes, config refactor |
| `services/auth_service.py` | Password strength, remember me, breach check integration |
| `services/election_service.py` | Dashboard stats, pagination, search |
| `services/candidate_service.py` | Bulk approve/reject |
| `database/schema.sql` | Add `audit_log` table reference |
| `static/js/main.js` | Loading states, enhanced password meter, form improvements |
| `static/css/style.css` | Toast styles, loading spinners, active nav states |
| `templates/base.html` | Toast integration |
| `.env.example` | All new config vars |
| `requirements.txt` | Add: alembic, pydantic-settings, sentry-sdk, reportlab |
