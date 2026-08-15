---
name: manage-repository-catalog
description: Create, inspect, and update the canonical Repository Catalog at `.workbench/repositories.yaml`. Use when asked to discover repo directories under `repos/`, create a missing catalog, add or remove repositories known to the project workspace, or update stable `repo_id` identities or checkout paths. Catalog membership does not grant AI access, require codebase indexing, or describe integrations. Do not use merely to regenerate `.code-workspace` from an unchanged catalog.
---

# Manage Repository Catalog

Maintain the canonical inventory of repositories known to the project workspace. Keep access policy, indexing configuration, integrations, and generated knowledge outside this catalog.

## Terminology

- Call each direct child directory under `repos/` a **workspace repository** or **repo**. Expect it to be a Git checkout, but allow an explicitly cataloged non-Git directory with a warning.
- Call a repo listed in `.workbench/repositories.yaml` a **cataloged repository**.
- Do not confuse a workspace repository with repository-pattern classes or data repositories inside source code.

## Schema

Use only schema version 1:

```yaml
schema_version: 1

repositories:
  - repo_id: repo_customer_portal
    path: repos/customer-portal
```

- Set `repo_id` to a stable, unique identifier matching `repo_<snake_case_name>`.
- Set `path` to a unique workspace-relative direct child of `repos/`.
- Do not add access, indexing, tool, remote, ownership, description, component, or integration fields to schema version 1.
- Represent a valid empty catalog as `repositories: []`.

## Catalog semantics

- Catalog a repository when the project workspace should know that it exists and other workspace data may need to reference it.
- Include supporting repositories such as test environments, fixtures, documentation, skills, extensions, or automation when they belong to the project workspace.
- Do not infer read, write, execute, indexing, or runner permissions from catalog membership.
- Do not omit a project repository merely because codebase knowledge does not need to index it.

## Workflow

1. Read the root instructions and the existing catalog, if present.
2. Discover candidates only from direct child directories of `repos/`. Record whether each candidate has a `.git` file or directory; do not silently omit a non-Git candidate.
3. Compare candidates with cataloged entries. Do not inspect or modify files inside candidates merely to catalog them.
4. Add or remove only repositories explicitly named by the user. If project membership is ambiguous, present candidates and ask which ones belong in the catalog.
5. Create or update the catalog with schema version 1. Preserve unaffected entries and their order; append new entries in the order requested.
6. Validate identities, paths, uniqueness, direct-child scope, and Git-checkout warnings with `python3 tooling/generate_vscode_workspace.py --check`. A stale `.code-workspace` result is expected immediately after a valid catalog change.
7. After the catalog is valid, use `$generate-vscode-workspace` to regenerate and check `.code-workspace`.

## Constraints

- Never catalog every discovered directory automatically.
- Never create, edit, delete, or rename files inside `repos/*`.
- Never initialize Git in a candidate directory as part of cataloging.
- Do not remove an unaffected cataloged repository.
- Keep derived knowledge and policy in separate files that reference `repo_id`.
