---
name: manage-repository-registry
description: Create, inspect, and selectively update this workspace's repository registry at `.workbench/repositories.yaml`. Use when asked to discover repo candidates under `repos/`, create a missing registry, register selected repos, unregister entries, or update repository identifiers or paths. Do not use merely to regenerate `.code-workspace` from an unchanged registry.
---

# Manage Repository Registry

Maintain the selective list of repos that participate in root workspace coordination. Never assume every repo under `repos/` should be registered.

## Terminology

- Call each direct child directory under `repos/` a **repo** or **repository**. Expect it to be a Git checkout, but allow an explicitly selected non-Git directory with a warning.
- Call a repo listed in `.workbench/repositories.yaml` a **registered repository**.
- Treat an unlisted repo as intentionally unregistered unless the user says otherwise.

## Schema

Use only schema version 1:

```yaml
schema_version: 1

repositories:
  - id: customer-portal
    path: repos/customer-portal
```

- Set `id` to a stable, unique kebab-case identifier.
- Set `path` to a unique workspace-relative direct child of `repos/`.
- Do not add service, remote, ownership, description, or integration fields to schema version 1.
- Represent a valid empty registry as `repositories: []`.

## Workflow

1. Read the root instructions and the existing registry, if present.
2. Discover candidates only from direct child directories of `repos/`. Record whether each candidate has a `.git` file or directory; do not silently omit a non-Git candidate.
3. Compare candidates with registered entries. Do not inspect or modify files inside candidate repos merely to register them.
4. Add or remove only repositories explicitly named by the user. If the requested set is ambiguous, present candidates and ask which ones to register.
5. Create or update the registry with schema version 1. Preserve unaffected entries and their order; append newly registered entries in the order requested.
6. Validate IDs, paths, uniqueness, direct-child scope, and Git-checkout warnings with `python3 tooling/generate_vscode_workspace.py --check`. A stale `.code-workspace` result is expected immediately after a valid registry change.
7. After the registry is valid, use `$generate-vscode-workspace` to regenerate and check `.code-workspace`.

## Constraints

- Never register all discovered repos automatically.
- Never create, edit, delete, or rename files inside `repos/*`.
- Never initialize Git in a candidate directory as part of registration.
- Do not remove an unaffected registered entry.
- Keep registry metadata separate from future integration or dependency mappings.
