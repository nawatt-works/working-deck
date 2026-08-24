# Mission Control Guidelines

These instructions apply to files under `_Mission-Control/`. They supplement the
root `AGENTS.md` after bootstrap, or `AGENTS_EXAMPLE.md` while this is still an
unconfigured starter. They do not replace the root instructions or grant
additional access to any work repository.

## Purpose and boundaries

- `_Mission-Control/` is the workspace control plane. It contains shared
  workspace metadata, contracts, and automation used to coordinate work across
  repositories.
- Production source code and repository-owned tests, fixtures, configuration,
  and build artifacts belong in the appropriate work repository under `repos/`,
  not here.
- Root instruction and policy files remain at the workspace root so AI harnesses
  can discover them. Harness-owned directories such as `.agents/`, `.claude/`,
  or `.cursor/` also remain wherever their harness requires them.
- Do not treat every note, plan, prompt, log, or generated artifact as Mission
  Control data. Keep harness-owned artifacts in the owning harness's documented
  location and temporary work in the harness or system temporary directory.

## Areas

- `workspace-meta/` holds public workspace metadata and contracts that multiple
  consumers may share. Read `workspace-meta/README.md` before adding a metadata
  type or editing a contract.
- `tooling/` holds automation that maintains the workspace control plane. It
  must not write into work repositories unless the user explicitly requests a
  change to those repositories.

## Working modes

- Work may be completed directly by the active AI harness when that is the
  simplest safe approach.
- Use planning, handoff documents, or delegated agents only when the task
  benefits from them and the active harness and user authorization permit them.
- Do not create a blueprint, dispatch manifest, task log, or handoff merely to
  satisfy a fixed ceremony. Create durable coordination state only when another
  producer, session, or automation needs it.
- The user is the final decision-maker. Repository access, write permission,
  execution permission, and remote Git operations remain governed by the root
  instructions, `GIT_POLICY.md`, and repository-specific guidance.

## Paths and validation

- Write paths relative to the workspace root in durable metadata and
  instructions unless a contract explicitly requires another form.
- Run Mission Control commands from the workspace root, for example:

  ```bash
  python3 _Mission-Control/tooling/validate_repository_catalog.py
  python3 _Mission-Control/tooling/repos_status.py
  python3 _Mission-Control/tooling/validate_handoff.py
  ```

## Language

- Use Thai by default when speaking with the user and for human-facing
  documentation.
- Keep technical identifiers, source code, commands, and text that must match an
  external system in their required language.
- Follow an explicit user request for another language.
