# Global Git Upstream Safety

These rules apply to every Git repository. Their purpose is to prevent
unintended or destructive remote writes, and a local branch from accidentally
pushing to a differently named remote branch.

## Default restriction for remote pushes

- By default, do not push any ref (branch or tag) to any Git remote.
- Fetching or pulling from remotes is allowed; this restriction applies only to
  push operations.
- A repository-level or more specific `AGENTS.md`/`AGENTS.override.md` may
  explicitly allow remote pushes for that project. The permission must be
  written in project guidance; the existence of a remote, an upstream, or a
  general request to "push" is not by itself an override.
- A project override should state the permission explicitly and may limit it to
  named remotes, for example:

  ```md
  ## Git Push Override

  - Codex may push to Git remotes in this project.
  ```

- An override allowing ordinary pushes does not disable the branch/upstream
  name-matching checks below, and does not by itself permit force pushes or ref
  deletion — those require the separate, explicit permission described next.

## Force pushes and ref deletion require separate permission

- Force pushing (`--force`, `--force-with-lease`, `--force-if-includes`) and
  remote ref deletion (`--delete`, or a refspec such as
  `:refs/heads/<branch>` / `:refs/tags/<tag>`) are destructive, history-altering
  operations. A plain push override does not grant either.
- These require their own explicit statement in project guidance, and may be
  scoped narrowly, for example:

  ```md
  ## Git Push Override

  - Codex may push to Git remotes in this project.
  - Codex may force-push to `feature/*` branches only.
  ```

- Without that separate statement, treat force push and remote ref deletion as
  prohibited even when ordinary pushes are allowed.
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

- These rules do not globally prohibit work on or pushes to `main`, `master`,
  or another branch after project guidance explicitly allows remote pushes and
  that repository's workflow and the user's request allow the specific push.
- Without a project-level override, remote pushes remain prohibited regardless
  of the target branch or remote name.
- When an override exists, branch-name mismatches, relying on a mismatched
  upstream as a push destination, and unscoped force pushes or ref deletion all
  remain prohibited unless separately and explicitly granted.
