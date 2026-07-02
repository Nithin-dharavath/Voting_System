---

description: Commit, push, create PR, merge, clean up, and create the next roadmap branch automatically
allowed-tools: Read, Bash, mcp__github__create_pull_request, mcp__github__merge_pull_request, mcp__github__delete_branch
------------------------------------------------------------------------------------------------------------------------

# /ship-feature

Ships the current roadmap feature branch, merges it, deletes it, then creates the **next roadmap branch** automatically.

## Roadmap order

The next branch is chosen from this ordered task list:

* `1.1` Enforce JWT_SECRET in production
* `1.2` Add security headers middleware
* `1.3` Add S3 upload support
* `1.4` Harden CORS for production
* `1.5` Multi-stage Docker build
* `1.6` Production docker-compose
* `1.7` Nginx reverse proxy config
* `1.8` EC2 user-data script
* `1.9` Update env templates
* `1.10` Local verification
* `2.1` RDS MySQL Instance
* `2.2` S3 Bucket
* `2.3` IAM Role for EC2
* `2.4` ECR Repository
* `2.5` Security Group for EC2
* `2.6` EC2 Instance
* `2.7` Elastic IP
* `2.8` Secrets Manager
* `3.1` Extend GitHub Actions workflow
* `3.2` Add GitHub Secrets
* `3.3` Test the pipeline
* `4.1` Push code trigger
* `4.2` SSH into EC2
* `4.3` Run database migrations
* `4.4` Seed database
* `4.5` Initial SSL certificate
* `4.6` End-to-end functional test

## Branch format

Current branch **must** be:

```text
feature/<task-title-slug>
```

Examples:

* `feature/add-s3-upload-support`
* `feature/harden-cors-for-production`
* `feature/multi-stage-docker-build`

## Step 1 — Detect branches

Determine the repository default branch and store it as `DEFAULT_BRANCH`.

Run:

```bash
git branch --show-current
```

Store it as `CURRENT_BRANCH` and also `OLD_FEATURE_BRANCH`.

If `CURRENT_BRANCH` is the default branch, stop and say:

```text
You're currently on the default branch.
Switch to a roadmap feature branch before running /ship-feature.
```

## Step 2 — Validate roadmap branch and extract current task

`CURRENT_BRANCH` must match one of:

```text
feature/<task-id-with-dashes>-<task-title-slug>
feature/<task-title-slug>
```

Extract the title slug from the branch name (everything after `feature/`).
Find the matching roadmap task by slug-matching each roadmap title:

* `feature/1-2-add-security-headers-middleware` → `CURRENT_TASK_ID=1.2`
* `feature/2-6-ec2-instance` → `CURRENT_TASK_ID=2.6`
* `feature/harden-cors-for-production` → look up slug `harden-cors-for-production` against roadmap titles

**If the branch has a task ID prefix** (e.g. `1-2-`), parse `CURRENT_TASK_ID` from it directly.

**If the branch has no task ID prefix**, extract the slug from `feature/<slug>` and find the matching roadmap entry by converting each roadmap title to kebab-case and comparing:
1. Take a roadmap title (e.g. `Add S3 upload support`)
2. Lowercase it → `add s3 upload support`
3. Replace spaces with hyphens → `add-s3-upload-support`
4. Compare to the extracted slug

The first match sets `CURRENT_TASK_ID`. If no match is found, stop with:

```text
Could not match branch slug "<slug>" to any roadmap entry.
Available tasks: feature/<task-id>-<task-title-slug>
```

If the branch does not start with `feature/`, stop and say:

```text
Current branch does not match the roadmap branch format.
Use: feature/<task-id-with-dashes>-<task-title-slug>
Or:  feature/<task-title-slug>
Then run /ship-feature again.
```

## Step 3 — Generate commit message

Run:

```bash
git diff --staged
git diff
git log DEFAULT_BRANCH..HEAD --oneline
```

If a matching spec exists in `.claude/specs/`, use it. If not, infer the feature from the code changes and commit history.

Generate a Conventional Commit message using one of:

* `feat:`
* `fix:`
* `chore:`
* `docs:`
* `refactor:`
* `test:`
* `perf:`

Rules:

* lowercase
* no period at the end
* under 72 characters
* describe what the user can now do, not what the code does

Also generate `PR_TITLE` as plain English without the Conventional Commit prefix.

## Step 4 — Commit

Run:

```bash
git add .
git status --short
```

If there are no changes to commit, stop and say:

```text
No changes detected.
Nothing to commit.
```

Otherwise run:

```bash
git commit -m "<COMMIT_MESSAGE>"
```

Report:

```text
✓ Committed — <COMMIT_MESSAGE>
```

## Step 5 — Push

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

## Step 6 — Create or reuse PR

If GitHub MCP is not connected, stop and say:

```text
GitHub MCP is not connected. Run /mcp to check connection.
```

If a PR already exists for `CURRENT_BRANCH`, reuse it. Otherwise create one from `CURRENT_BRANCH` into `DEFAULT_BRANCH`.

Use `PR_TITLE` as the title.

### PR body if a spec exists

```markdown
## What this PR does
<one paragraph from the spec overview>

## Changes
<bullet list of changed files with one-line descriptions>

## Definition of done
<spec checklist with completed items marked [x]>

## How to test
<testing steps from the spec>
```

### PR body if no spec exists

```markdown
## What this PR does
<one paragraph describing the completed feature>

## Changes
<bullet list of changed files with one-line descriptions>

## How to test
1. Run the app or tests.
2. Verify the new functionality.
3. Include any manual verification steps.
```

Report:

```text
✓ PR created — <PR URL>
```

## Step 7 — Merge PR

Merge the PR using **Squash Merge**.

If PR creation failed, stop.
If merge conflicts exist, stop and ask the user to resolve them first.

Report:

```text
✓ PR merged to DEFAULT_BRANCH
```

## Step 8 — Delete remote branch

Delete `OLD_FEATURE_BRANCH` via GitHub MCP.

If it is already deleted, ignore the error.

Report:

```text
✓ Remote branch deleted
```

## Step 9 — Switch to default branch and pull

Run:

```bash
git checkout DEFAULT_BRANCH
git pull origin DEFAULT_BRANCH
```

Report:

```text
✓ Switched to DEFAULT_BRANCH — up to date
```

## Step 10 — Delete local branch

Run:

```bash
git branch -D OLD_FEATURE_BRANCH
```

If it no longer exists locally, ignore the error.

Report:

```text
✓ Local branch deleted
```

## Step 11 — Find the next roadmap task

Using the roadmap order at the top of this file, find the task immediately after `CURRENT_TASK_ID`.

Examples:

* `1.1` → `1.2`
* `1.2` → `1.3`
* `2.8` → `3.1`
* `4.5` → `4.6`

Store:

* `NEXT_TASK_ID`
* `NEXT_TASK_TITLE`

If there is no next task, do not create a branch. Report:

```text
✓ Roadmap complete — no next feature branch created
```

## Step 12 — Create next roadmap branch

If a next task exists, generate:

```text
feature/<next-task-title-kebab-case>
```

Examples:

* `1.3` + `Add S3 upload support` → `feature/add-s3-upload-support`
* `2.6` + `EC2 Instance` → `feature/ec2-instance`

Store it as `NEXT_BRANCH`.

Run:

```bash
git checkout -b NEXT_BRANCH
```

If it already exists locally, stop and say:

```text
The next roadmap branch already exists locally: NEXT_BRANCH
Switch to it manually or delete it before continuing.
```

Set `CURRENT_BRANCH = NEXT_BRANCH`.

Report:

```text
✓ Created new feature branch — CURRENT_BRANCH
✓ Next roadmap task — NEXT_TASK_ID: NEXT_TASK_TITLE
```

## Final summary

If a next branch was created:

```text
────────────────────────────────────────

/ship-feature complete

✓ Committed — <COMMIT_MESSAGE>
✓ Pushed — <OLD_FEATURE_BRANCH>
✓ PR created and merged
✓ Remote branch deleted
✓ Switched to DEFAULT_BRANCH
✓ Local branch deleted
✓ Created new feature branch — <CURRENT_BRANCH>
✓ Next roadmap task — <NEXT_TASK_ID>: <NEXT_TASK_TITLE>

Next: implement <NEXT_TASK_ID> on <CURRENT_BRANCH>

────────────────────────────────────────
```

If there is no next task:

```text
────────────────────────────────────────

/ship-feature complete

✓ Committed — <COMMIT_MESSAGE>
✓ Pushed — <OLD_FEATURE_BRANCH>
✓ PR created and merged
✓ Remote branch deleted
✓ Switched to DEFAULT_BRANCH
✓ Local branch deleted
✓ Roadmap complete — no next feature branch created

Next: deployment roadmap is complete

────────────────────────────────────────
```

## Rules

* Never commit directly to the default branch.
* Always use **Squash Merge**.
* Always delete both the remote and local shipped branch.
* Always create the **next roadmap branch** unless the roadmap is complete.
* The next branch must come from the roadmap order in this file, not from git diff or a generic name.
* The current branch must follow the roadmap branch naming format.
* If GitHub MCP is not connected, stop with:

```text
GitHub MCP is not connected. Run /mcp to check connection.
```

* If push fails due to no upstream, use:

```bash
git push -u origin CURRENT_BRANCH
```

* Never proceed to merge if PR creation fails.
* Never fail only because a spec file is missing.
* If a spec is incomplete, use the code changes as the source of truth.
* If a PR already exists for the current branch, reuse it.
* Stop only for critical blockers such as:

  * merge conflicts
  * no changes to commit
  * GitHub MCP unavailable
  * invalid roadmap branch format
  * unable to determine the next roadmap task
