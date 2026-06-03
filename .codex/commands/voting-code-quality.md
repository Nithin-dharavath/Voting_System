---
description: Run parallel security and quality review for a voting feature.
allowed-tools: Bash(git diff), Bash(git diff --staged)
---

# Code Review Feature

Feature argument: `$ARGUMENTS`

If no argument is provided, stop:

`Please provide a spec name. Usage: /code-review-feature <spec-name> e.g. /code-review-feature 03-admin-login`

## Preflight

1. Run `git diff`.
2. Run `git diff --staged`.
3. Combine both diffs.
4. Confirm `.codex/specs/$ARGUMENTS.md` exists.

Stop if:

- both diffs are empty: `No changes detected. Implement the feature before running code review.`
- the spec is missing: `Spec file not found at .codex/specs/$ARGUMENTS.md.`

## Review

Run both reviewers in parallel with the same diff and spec:

- `security-reviewer`: changed code only, security findings only.
- `quality-reviewer`: changed code only, maintainability and framework-fit findings only.

## Report

Return:

```md
## Code Review Report: $ARGUMENTS

Security Findings:
<security-reviewer summary>

Quality Findings:
<quality-reviewer summary>

Action Plan:
1. <highest priority fix>

Verdict: APPROVED | APPROVED WITH SUGGESTIONS | CHANGES REQUESTED
```

After the report, ask:

`Do you want me to implement the action plan now?`

Do not edit files until the user explicitly approves.
