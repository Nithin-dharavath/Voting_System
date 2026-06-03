---
description: Write and run targeted pytest tests for a voting feature spec.
allowed-tools: Bash(python -m pytest)
---

# Test Feature

Feature argument: `$ARGUMENTS`

If no argument is provided, stop:

`Please provide a spec name. Usage: /test-feature <spec-name> e.g. /test-feature 05-student-election-list`

If `.codex/specs/$ARGUMENTS.md` does not exist, stop:

`Spec file not found at .codex/specs/$ARGUMENTS.md.`

## Step 1: Write Tests

Invoke `test-writer` with:

- spec: `.codex/specs/$ARGUMENTS.md`
- source structure: `app.py`, `database/`, `templates/`, `tests/`
- output: `tests/test_$ARGUMENTS.py`
- rule: tests come from spec behavior, not implementation internals

Wait until the test file exists before continuing.

## Step 2: Run Tests

Invoke `test-runner` with:

- file: `tests/test_$ARGUMENTS.py`
- command: `python -m pytest tests/test_$ARGUMENTS.py -v`
- rule: run only this file

Do not fix product code in this command.

## Final Output

```md
## Testing Pipeline Report: $ARGUMENTS

Tests written:
- <test and behavior>

Results:
<test-runner summary>

Verdict: Ready for code review | Needs fixes
```
