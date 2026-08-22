---
name: add-workspace-repository
description: Onboard one catalog v1 repository into the default `repos/` source area end to end — place it under `repos/`, set its Git tracking mode in `.gitignore`, classify it as `own` or `client` in `AGENTS.md`, and register it in the Repository Catalog. Use when adding, cloning, or adopting a repository under `repos/`, or when `repos_status.py` reports a `gitlink` or `untracked` state. Do not use merely to edit the catalog, which `$manage-repository-catalog` owns.
---

# Add Workspace Repository

Adding a repository under catalog schema v1 touches four places that must agree: the directory under `repos/`, the root `.gitignore`, the repository class in `AGENTS.md`, and the Repository Catalog. Getting one wrong is silent, so drive all of them together and verify with `repos_status.py`.

## Tracking modes

A repository under `repos/` must end in exactly one of two correct states.

- **external** — it has its own `.git` and stays ignored by the root repository. This is the normal case. Committing it into the root would produce a `gitlink` that clones as an empty directory.
- **internal** — it has no `.git` of its own and is opted in to the root repository with `!repos/<directory>/` in `.gitignore`. Without that line the work is tracked nowhere at all.

The other two combinations are errors that `python3 tooling/repos_status.py` reports.

## Workflow

1. Read the root `AGENTS.md` for the project's default repository class, and read `GIT_POLICY.md` if the class is unclear.
2. Determine how the repository arrives. If it must be cloned, ask the user for the remote URL and clone it into `repos/<directory>` yourself; never assume a URL.
3. Inspect whether the directory has its own `.git`. Ask the user which mode is intended when the directory is empty or newly created.
4. For an internal repository, add `!repos/<directory>/` to the opt-in block in `.gitignore`. For an external repository, make sure no such line exists for it.
5. Ask for the repository class when it is not obvious, and state the project default in the question. Add a row to the Repository Classes table in `AGENTS.md` only when the class differs from the default; leave the table untouched otherwise.
6. Use `$manage-repository-catalog` to add the catalog entry. Do not hand-edit `workspace-meta/repositories.yaml` in this skill.
7. Run `python3 tooling/repos_status.py` and confirm the new repository reports `external` or `internal` with no errors.
8. Report the resulting mode, class, `repo_id`, and any warning that remains.

## Constraints

- Never create, edit, delete, or rename files inside the repository being added, including its `.gitignore` and any AI harness configuration.
- Never run `git init` inside a directory under `repos/` to change its tracking mode; ask the user instead.
- Never add `AGENTS.md`, `CLAUDE.md`, `.agents/`, `.claude/`, `workspace-meta/`, or legacy `workbench/` content to a repository under `repos/`.
- Never remove or weaken `repos/*` in `.gitignore` to make a repository visible; use a single `!repos/<directory>/` opt-in line.
- Treat a repository as `client` whenever ownership is unconfirmed, and never record `own` without the user saying so.
- Do not record a remote URL, description, or class inside `workspace-meta/repositories.yaml`; schema version 1 holds only `repo_id` and `path`.
- Stop and report rather than guessing when the directory is missing, is not a repository, or already has a conflicting catalog entry.
