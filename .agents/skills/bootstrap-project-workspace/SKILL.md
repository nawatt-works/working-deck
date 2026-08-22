---
name: bootstrap-project-workspace
description: Turn a fresh copy of the Working Deck starter into a configured project workspace by interviewing the user and generating the project-specific files, chiefly `AGENTS.md` with its repository class defaults. Use once per project, right after copying the starter, or when `AGENTS.md` is still missing while `AGENTS_EXAMPLE.md` is present. Do not use to add or catalog individual repositories.
---

# Bootstrap Project Workspace

Convert the starter's template files into the instructions for one concrete project. The starter ships rules that are identical everywhere; this skill fills in only what differs per project.

## Scope

Bootstrap captures the project's **posture**, not its repository list. A new project usually does not know its repositories yet, and repositories keep arriving during development. Leave the catalog empty and let `$add-workspace-repository` handle each repository as it appears.

## Workflow

1. Confirm the workspace is an unbootstrapped starter: `AGENTS_EXAMPLE.md` exists and `AGENTS.md` does not. If `AGENTS.md` already exists, stop and report that the workspace is already bootstrapped.
2. Read `AGENTS_EXAMPLE.md`, `README.md`, and `GIT_POLICY.md` before writing anything.
3. Ask the user for the project posture. Keep it to these questions and offer the stated default:
   - Project name.
   - Language for conversation and human-facing output such as `README.md`; default Thai. Instruction files stay in English regardless of this answer, so do not ask about them.
   - Default repository class for repositories under `repos/`; default `client`.
   - Whether the root workspace repository may be pushed to a remote; default yes, class `own`.
4. Rename `AGENTS_EXAMPLE.md` to `AGENTS.md` with `git mv` so the project keeps exactly one instruction file.
5. Fill the Repository Classes section in `AGENTS.md` with the answers. Record the default class and the root workspace class. Leave the per-repository table empty when no repository differs from the default.
6. Adjust only the human-facing half of the Language section in `AGENTS.md` when the user chose a language other than the starter default. Leave the instruction-file half unchanged, and do not translate `AGENTS.md`, `GIT_POLICY.md`, or any `SKILL.md`.
7. Leave `workspace-meta/repositories.yaml` as `repositories: []` unless repositories already exist under `repos/`. If they do, stop and tell the user to run `$add-workspace-repository` for each one rather than cataloging them here.
8. Verify the result by running, from the workspace root:
   - `python3 tooling/validate_repository_catalog.py`
   - `python3 tooling/repos_status.py`
   - `python3 tooling/validate_handoff.py`
9. Report what was generated, the recorded defaults, and that repositories are added later with `$add-workspace-repository`.

## Constraints

- Do not invent repositories, `repo_id` values, remotes, or catalog entries.
- Do not create speculative folders under `workspace-meta/`; it is for workspace-owned metadata and contracts, not a catch-all artifact area.
- Keep `workspace-meta/handoff/` as the starter ships it, holding only its `README.md`. Work items are created later, when work actually crosses from one role to another through the Working Deck handoff contract.
- Do not weaken `repos/*` in `.gitignore`. The default-deny posture is fixed for every project regardless of the answers.
- Do not create, edit, delete, or rename files under `repos/*`.
- Do not add AI harness configuration to any repository under `repos/`.
- Do not delete `GIT_POLICY.md` or rewrite its per-class rules; only the classification in `AGENTS.md` is project-specific.
- Do not translate instruction or contract files into the conversation language. They are English for model and tool compatibility, which is independent of how the AI speaks to the user.
- Ask rather than guess when an answer is missing; never assume a repository is `own`.
