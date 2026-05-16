---
description: Create a spec file and feature branch for the next Online Voting roadmap step
argument-hint: "Step number and feature name e.g. 2 registration"
allowed-tools: Read, Write, Glob, Bash(git:*)
---

You are a senior developer spinning up a new feature for the Online Voting System.
Always follow the rules in README.md, docs/project-overview.md, docs/database.md, docs/api-contracts.md, docs/conventions.md, and app.py.

User input: $ARGUMENTS

## Purpose

Create a clean feature branch and a single spec file for the next roadmap step.
Keep the workflow strict, minimal, and deterministic.
Do not implement code.
Do not expand scope beyond the spec.
Do not duplicate existing roadmap work.

## Step 1 — Verify clean working tree

Run `git status --short`.

If there is any output:
- stop immediately,
- tell the user to commit or stash changes first,
- do not continue.

## Step 2 — Parse arguments

From `$ARGUMENTS`, extract:

1. `step_number`
- zero-padded to 2 digits.
- Examples: `2 -> 02`, `11 -> 11`.

2. `feature_title`
- human-readable title in Title Case.
- Examples: `Registration`, `Login and Logout`.

3. `feature_slug`
- lowercase kebab-case.
- only `a-z`, `0-9`, and `-`.
- maximum 40 characters.
- Examples: `registration`, `login-logout`.

4. `branch_base`
- `feature/<feature_slug>`.

If the arguments are ambiguous, ask for clarification before continuing.

## Step 3 — Check branch availability

List branches with:
```bash
git branch --all --no-color
```

If `branch_base` already exists, append a numeric suffix:
- `feature/<feature_slug>-01`
- `feature/<feature_slug>-02`
- etc.

Use the first available branch name.

## Step 4 — Switch to main and sync

Run:
```bash
git checkout main
git pull origin main
```

If `main` does not exist locally, stop and report the issue.

## Step 5 — Create the feature branch

Run:
```bash
git checkout -b <branch_name>
```

## Step 6 — Inspect the codebase

Before writing the spec, read:

- `README.md`
- `docs/project-overview.md`
- `docs/database.md`
- `docs/api-contracts.md`
- `docs/conventions.md`
- `app.py`
- all existing files in `.claude/specs/`

Use this inspection to:
- avoid duplicating existing work,
- match current project conventions,
- confirm whether the roadmap step is already complete,
- verify current route names, framework style, database config source, table names, and field names.

If the requested step is already marked complete in docs or roadmap files, warn the user and stop.

## Step 7 — Draft the spec

Write a spec file using this exact structure:

---
# Spec: <feature_title>

## Overview
One paragraph explaining what this feature does and why it exists now in the Online Voting roadmap.

## Depends on
List the previous step(s) this feature requires. If none, state `None`.

## Routes
List every new route needed:
- `METHOD /path` — description — access level (public/logged-in/admin)

If no new routes are needed, state `No new routes`.

## Database changes
List any new tables, columns, constraints, indexes, seed data, or enum values needed.
Verify against `docs/database.md` and `database/` behavior before writing this section.
If none, state `No database changes`.

## Templates
- **Create:** list new templates with full paths.
- **Modify:** list existing templates and what changes.

If none, state `No template changes`.

## Files to change
List every existing file that will be modified.

## Files to create
List every new file that will be created.

If none, state `No new files`.

## New dependencies
List any new pip packages only if required.
If none, state `No new dependencies`.

## Rules for implementation
Include specific constraints Claude must follow.

Always include:
- No SQLAlchemy or ORMs.
- Parameterised queries only.
- Passwords hashed with `werkzeug`.
- Use CSS variables, never hardcode hex values.
- All templates extend `base.html`.
- Do not hardcode database passwords, JWT secrets, upload paths, server URLs, or admin credentials.
- Validate uploaded files, rename them safely, and store only file paths.
- Keep changes minimal and aligned with the existing app structure.
- Do not introduce new architecture unless the spec explicitly requires it.

## Definition of done
List specific, testable checks that can be verified by running the app.
Each item must be observable and unambiguous.
---

## Step 8 — Save the spec

Save the file to:

`.claude/specs/<step_number>-<feature_slug>.md`

## Step 9 — Report results

Print exactly:

```text
Branch:    <branch_name>
Spec file: .claude/specs/<step_number>-<feature_slug>.md
Title:     <feature_title>
```

Then say:

`Review the spec at .claude/specs/<step_number>-<feature_slug>.md then enter Plan Mode with Shift+Tab twice to begin implementation.`

Do not print the full spec in chat unless explicitly asked.