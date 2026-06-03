---
description: Create a feature branch and `.codex/specs` file for the next Online Voting roadmap step.
argument-hint: "Step number and feature name, e.g. 11 results publishing"
allowed-tools: Read, Write, Glob, Bash(git:*)
---

# Create Spec

User input: `$ARGUMENTS`

Create a branch and spec only. Do not implement product code.

## Preflight

1. Run `git status --short`.
2. If output is not empty, stop and ask the user to commit or stash first.
3. Parse:
   - step number, zero-padded to two digits
   - feature title in Title Case
   - feature slug in lowercase kebab-case, max 40 chars
   - branch name `feature/<feature-slug>`, with numeric suffix if needed

Ask one focused question if the input is ambiguous.

## Branch

1. Run `git branch --all --no-color`.
2. Run `git checkout main`.
3. Run `git pull origin main`.
4. Run `git checkout -b <branch_name>`.

Stop and report if `main` is unavailable or sync fails.

## Inspect Before Writing

Read:

- `README.md`
- `docs/project-overview.md`
- `docs/database.md`
- `docs/api-contracts.md`
- `docs/conventions.md`
- `app.py`
- existing `.codex/specs/*.md`

Use this to avoid duplicate roadmap work and match current routes, table names, field names, and conventions.

## Spec Template

Save to `.codex/specs/<step>-<slug>.md`:

```md
# Spec: <feature_title>

## Overview
<one paragraph>

## Depends on
<steps or None>

## Routes
- `<METHOD> <path>` - <description> - <access>

## Database changes
<tables, columns, constraints, indexes, seed data, or No database changes>

## Templates
- Create: <paths or None>
- Modify: <paths or None>

## Files to change
<existing files or None>

## Files to create
<new files or No new files>

## New dependencies
<packages or No new dependencies>

## Rules for implementation
- No SQLAlchemy or ORMs.
- Use `get_db_cursor()` and parameterized SQL.
- Hash passwords with `werkzeug.security`.
- Use CSS variables from `static/css/style.css`.
- All templates extend `base.html`.
- Store secrets and paths in environment/config.
- Validate uploads, safely rename files, store only file paths.
- Keep changes minimal and aligned with the existing app.

## Definition of done
- <observable, testable check>
```

## Final Output

```text
Branch:    <branch_name>
Spec file: .codex/specs/<step>-<slug>.md
Title:     <feature_title>
```

Then say:

`Review the spec, then enter Plan Mode with Shift+Tab twice to begin implementation.`
