---

description: Commit, push, create PR, merge, and clean up after a feature is complete
allowed-tools: Read, Bash, mcp__github__create_pull_request, mcp__github__merge_pull_request, mcp__github__delete_branch
------------------------------------------------------------------------------------------------------------------------

## Step 1 — Identify the default and current branch

Determine the repository's default branch (`main`, `master`, or another configured default) and store it as `DEFAULT_BRANCH`.

Run:

```bash
git branch --show-current
```

Store this as `CURRENT_BRANCH`.

If `CURRENT_BRANCH` is `DEFAULT_BRANCH`, stop and say:

```text
You're currently on the default branch.
Create a feature branch before running /ship-feature.
```

## Step 2 — Generate commit message

Run:

```bash
git diff --staged
git diff
git log DEFAULT_BRANCH..HEAD --oneline
```

If a matching spec exists in `.claude/specs/`, use it to understand the completed feature.

If no spec exists:

* Infer the feature from the Git diff, commit history, project structure, and source code.
* Never stop because a spec is missing.

Generate a Conventional Commit message:

* feat: new feature
* fix: bug fix
* chore: config or tooling
* docs: documentation only
* refactor: internal improvements
* test: tests only
* perf: performance improvements

Rules:

* Lowercase
* No period at the end
* Under 72 characters
* Describes what the user can now do, not what the code does

Good:

```text
feat: add delete expense button with confirmation dialog
```

Bad:

```text
feat: added DELETE route to app.py
```

## Step 3 — Commit

Run:

```bash
git add .
```

If there are no changes to commit, stop and say:

```text
No changes detected.
Nothing to commit.
```

Otherwise:

```bash
git commit -m "<generated-message>"
```

Report:

```text
✓ Committed — <message>
```

## Step 4 — Push to feature branch

Run:

```bash
git push
```

If push fails because no upstream exists, run:

```bash
git push -u origin CURRENT_BRANCH
```

Report:

```text
✓ Pushed — CURRENT_BRANCH
```

## Step 5 — Create PR via GitHub MCP

If GitHub MCP is not connected, stop and say:

```text
GitHub MCP is not connected. Run /mcp to check connection.
```

If a Pull Request already exists for `CURRENT_BRANCH`, reuse it.

Otherwise create a Pull Request from `CURRENT_BRANCH` into `DEFAULT_BRANCH`.

Title:

Plain English feature name.

Do not include the Conventional Commit prefix.

Example:

```text
Add delete expense functionality
```

### If a spec exists

Description:

```markdown
## What this PR does
<one paragraph from the spec overview>

## Changes
<bullet list of every file changed with one line description each>

## Definition of done
<copy the checklist from the spec and mark every completed item as [x]>

## How to test
<testing steps from the spec>
```

### If no spec exists

Generate:

```markdown
## What this PR does
<one paragraph describing the completed feature>

## Changes
<bullet list of every modified file with one line description each>

## How to test
1. Build or run the application.
2. Verify the new functionality.
3. Include any required manual verification steps.
```

Report:

```text
✓ PR created — <PR URL>
```

## Step 6 — Merge PR via GitHub MCP

Use the GitHub MCP server to merge the Pull Request.

Always use **Squash Merge**.

If PR creation failed, stop.

If merge conflicts exist, stop and ask the user to resolve them first.

Report:

```text
✓ PR merged to DEFAULT_BRANCH
```

## Step 7 — Delete remote branch via GitHub MCP

Delete `CURRENT_BRANCH` from GitHub.

If the branch has already been deleted, ignore the error.

Report:

```text
✓ Remote branch deleted
```

## Step 8 — Switch to the default branch and pull

Run:

```bash
git checkout DEFAULT_BRANCH
git pull origin DEFAULT_BRANCH
```

Report:

```text
✓ Switched to DEFAULT_BRANCH — up to date
```

## Step 9 — Delete local feature branch

Run:

```bash
git branch -D CURRENT_BRANCH
```

If the branch no longer exists locally, ignore the error.

Report:

```text
✓ Local branch deleted
```

## Final summary

Print:

```text
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌

/ship-feature complete

✓ Committed — <message>
✓ Pushed — <branch>
✓ PR created and merged
✓ Remote branch deleted
✓ Switched to DEFAULT_BRANCH
✓ Local branch deleted

Next: run /create-spec for the next feature

╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
```

## Rules

* Never commit directly to the repository's default branch.
* Always detect the repository's default branch automatically.
* Always use Squash Merge.
* Always delete both the remote and local feature branch after merging.
* If GitHub MCP is not connected, stop and say:

  ```
  GitHub MCP is not connected. Run /mcp to check connection.
  ```
* If push fails due to no upstream, use:

  ```bash
  git push -u origin CURRENT_BRANCH
  ```
* Never proceed to merge if PR creation fails.
* Never fail solely because a spec file is missing.
* If a spec is incomplete, use the code changes as the source of truth.
* If automated tests do not exist, include manual verification steps in the PR.
* If a Pull Request already exists for the current branch, reuse it instead of creating a new one.
* Stop only for critical blockers such as merge conflicts, insufficient permissions, no changes to commit, or GitHub MCP being unavailable.
