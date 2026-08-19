# Website repository working agreements

## Editing scope

- Treat `/Users/daniellitt/Documents/GitHub/chocolitt.github.io` as the only writable project root for this website.
- Make all website edits in this repository. Do not edit the migration workspace, old site copies, build archives, or similarly named directories.
- Other directories may be inspected read-only when needed for reference, but copying changes back into this repository must be explicit and reviewable.
- Before changing files, confirm that `git rev-parse --show-toplevel` resolves to this repository. If it does not, stop and switch to this repository before continuing.

## Git and publishing

- The user owns the publishing workflow.
- Do not commit, push, force-push, open or merge pull requests, or trigger deployments unless the user explicitly overrides this rule for a specific task.
- Leave completed changes uncommitted in the working tree for the user to review, commit, and push.
- Read-only Git operations such as `git status`, `git diff`, and `git log` are allowed.
- At handoff, summarize changed files and verification performed, and remind the user that the changes are ready for their commit and push.
