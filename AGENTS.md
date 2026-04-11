# Repository Agent Routing

## Commit and publish workflow

- When the user asks to **generate a commit message**, **prepare a commit**, or mentions **commit/changelog** without asking to push to a remote, prefer the `commit_writer` subagent.
- When the user explicitly asks to **push code to a remote**, **publish changes**, **提交并推送**, or says **选择合适的agent推送代码到远端**, prefer the `repo_publisher` subagent.
- Both `commit_writer` and `repo_publisher` must read `docs/commit-and-changelog-guidelines.md` before generating any commit message.

## Safety rules for publish requests

- A direct user request to push code to a remote counts as explicit permission to run `git commit` and `git push` for the selected changes.
- Never use force push or history-rewrite commands unless the user explicitly asks for them.
- Never stage everything blindly. Stage only the files required for the selected commit scope.
- If the working tree mixes unrelated changes and the split is ambiguous, stop and ask the user which part should be published first.
- If the split is obvious (for example, product code changes plus `.codex/` tooling setup), prefer separate commits.

## Commit quality bar

- Commit messages must follow `docs/commit-and-changelog-guidelines.md`.
- `Log:` must describe user-visible or caller-visible outcomes, not internal refactors.
- `Test:` must be honest. If validation was not run, say `not-run (reason: ...)`.
