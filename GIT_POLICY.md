# Git Policy

These rules apply to every Git repository reachable from this workspace,
including the root workspace itself, every repository under `repos/`, and any
other source root that a project explicitly documents. Their purpose is to
prevent unintended or destructive remote writes, to keep a local branch from
pushing to a differently named remote branch, and to keep this workspace's
coordination artifacts out of work repositories.

## Repository classes

Every repository belongs to exactly one class. The root `AGENTS.md` declares the
project's default class and lists any repository that differs, keyed by
`repo_id` when one exists. Classification lives in the root `AGENTS.md` because
the AI harness isolation rules forbid adding instruction files inside work
repositories.

- `own` — the user owns this repository. Ordinary pushes are permitted only
  when the user asks for a push and the repository's workflow allows it.
- `client` — someone else owns this repository. Never push any ref.

When a repository's class is unknown or undeclared, treat it as `client`. A new
repository that nobody has classified yet is therefore push-protected by
default.

The root workspace repository is `own` unless the project states otherwise.
This classification does not authorize unsolicited pushes.

## Remote pushes

- Fetching and pulling are always allowed. Every restriction here applies only
  to operations that write to a remote.
- Do not push any ref (branch or tag) to any remote of a `client` repository.
  The existence of a remote, a configured upstream, write access, or a general
  request to "push" is not permission.
- For an `own` repository, ordinary pushes are permitted only after a user
  request to push, and still must pass every check in this document.
- Permission to push never implies permission to force-push or delete refs —
  those require the separate, explicit permission described next.

## Keep this workspace out of work repositories

- Never commit or push this workspace's coordination artifacts into a repository
  under `repos/`, regardless of class. This includes `AGENTS.md`, `CLAUDE.md`,
  `.agents/`, `.claude/`, and anything from `_Mission-Control/`.
- Run `python3 _Mission-Control/tooling/repos_status.py` before committing inside a repository
  under `repos/`. It reports pending coordination artifacts that would otherwise
  reach a work repository's history.
- Inspect the staged change set before every commit in a repository you do not
  own, and confirm every path belongs to the task the user asked for.

## Force pushes and ref deletion require separate permission

- Force pushing (`--force`, `--force-with-lease`, `--force-if-includes`) and
  remote ref deletion (`--delete`, or a refspec such as
  `:refs/heads/<branch>` / `:refs/tags/<tag>`) are destructive, history-altering
  operations. A plain push override does not grant either.
- These require their own explicit statement in the root `AGENTS.md`, and may be
  scoped narrowly, for example:

  ```md
  - `repo_internal_tools` may be force-pushed on `feature/*` branches only.
  ```

- Without that separate statement, treat force push and remote ref deletion as
  prohibited even for an `own` repository whose ordinary pushes are permitted.
- Never force-push or delete a ref in a `client` repository.
- Never use a force push to resolve a rejected push (e.g. a non-fast-forward
  error). Stop and report the conflict instead of overriding it.

## Branch and upstream names must match

- When a local branch has an upstream, the upstream branch name must exactly
  match the local branch name. The remote name may differ, but the branch path
  after `<remote>/` must be identical.
- Valid examples:
  - local `main` → `origin/main`
  - local `master` → `origin/master`
  - local `feature/example` → `origin/feature/example`
  - local `feature/example` → `upstream/feature/example`
- Invalid examples:
  - local `feature/example` → `origin/main`
  - local `fix/example` → `origin/feature/example`
- If the names differ, stop before pushing. Remove the incorrect upstream or
  replace it with a same-named remote branch. Never push through a mismatched
  upstream.

## Ref scope: branches and tags

- All restrictions above apply equally to branches (`refs/heads/*`) and tags
  (`refs/tags/*`). Creating, moving, or deleting a remote tag is a remote write
  like any other and follows the same default-deny and force/deletion rules.
- Tags have no upstream-tracking concept, so the branch/upstream name-matching
  checks do not apply to them. Instead, a tag push must always name the exact,
  intended tag in an explicit refspec — never rely on `git push --tags` or
  `--follow-tags`, which push multiple tags implicitly and can leak an
  unintended tag to the remote.

## Creating a branch from another remote branch

- Creating a feature branch from `origin/main`, `origin/master`, or any other
  differently named remote branch must not inherit that source as its upstream.
- Explicitly disable tracking when creating it, for example:

  ```bash
  git switch --no-track -c feature/example origin/main
  ```

- Immediately verify the result with `git branch -vv`. The new branch's
  upstream must be absent until its same-named remote branch is created.

## Checks before every push

- Resolve the current local branch name. Do not push from detached HEAD or when
  the branch name is ambiguous.
- Resolve the configured upstream, if present, and verify that its branch name
  exactly matches the current local branch name.
- Every push must specify an explicit refspec naming the exact ref. Do not run
  a bare `git push`, and do not use `--all`, `--mirror`, `--tags`, or
  `--follow-tags` — these depend on `push.default` or act across multiple refs
  at once, bypassing the explicit-destination checks below.
- Use a dry run with an explicit same-named destination:

  ```bash
  git push --dry-run <remote> HEAD:refs/heads/<current-local-branch>
  ```

- Inspect the dry-run destination before the real push. Do not proceed if it is
  not exactly the current local branch name.
- Perform the real push with the same explicit destination. Add upstream only
  when needed:

  ```bash
  git push -u <remote> HEAD:refs/heads/<current-local-branch>
  ```

- After pushing, verify that the same-named remote branch points to local
  `HEAD`:

  ```bash
  git ls-remote <remote> refs/heads/<current-local-branch>
  git rev-parse HEAD
  ```

  Compare the two SHAs; the push is only confirmed correct if they match.

## Submodules

- These rules apply independently inside every Git repository, including any
  Git submodule. A submodule has its own remotes, branches, and upstream
  tracking distinct from the parent repository — apply every rule above from
  within the submodule's own working directory before pushing from it, and do
  not assume a parent-repo override or upstream setup extends to it.

## Scope

- These rules do not prohibit work on or pushes to `main`, `master`, or another
  branch in an `own` repository, provided that repository's own workflow and the
  user's request allow the specific push.
- For a `client` repository, remote pushes remain prohibited regardless of the
  target branch, the remote name, or the access the credentials happen to grant.
- Branch-name mismatches, relying on a mismatched upstream as a push
  destination, and unscoped force pushes or ref deletion remain prohibited in
  every class unless separately and explicitly granted.
- A repository under `repos/`, or under another documented source root, may
  carry its own contributing guide or workflow documentation. Follow it in
  addition to this policy; where they conflict, stop and ask the user rather
  than choosing one.
