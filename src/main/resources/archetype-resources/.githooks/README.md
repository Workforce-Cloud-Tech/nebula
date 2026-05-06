# Git hooks

This directory contains Git hooks for this package.

## Pre-commit hook

The `pre-commit` hook runs **Spotless check** and **Checkstyle check** before each commit. If either fails, the commit is aborted.

### One-time setup

From the repository root, run:

```bash
git config core.hooksPath .githooks
```

Git will then use the hooks in this directory instead of `.git/hooks`. The hook is versioned with the repo so everyone gets the same checks.

### Fixing failures

- **Spotless**: run `./mvnw spotless:apply` to fix formatting, then commit again.
- **Checkstyle**: fix the reported issues in your code, then commit again.

### Skipping the hook (use sparingly)

To bypass the hook for a single commit (e.g. WIP):

```bash
git commit --no-verify -m "your message"
```

## Restoring default hooks

To use the default `.git/hooks` again:

```bash
git config --unset core.hooksPath
```
